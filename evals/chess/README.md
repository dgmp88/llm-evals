# Chess LLM Evaluation Plan - Static Position Approach

## Overview
Evaluate LLM chess playing ability by testing moves in static positions from games at different skill levels, rather than playing full games. This approach is cost-effective while maintaining evaluation precision.

## Project Structure

### Step 1: Game Generation
Generate Stockfish vs Stockfish games at multiple ELO levels to create evaluation positions.

#### 1.1 Strength Configuration
- **Target Skill Levels**: 5, 10, 15, 18, 20 (roughly equivalent to 1200, 1400, 1600, 1800, 2000+ ELO)
- **Games per Level**: 2 games = 10 total games
- **Engine Setup**: Stockfish with `Skill Level` parameter

**Skill Level to ELO Mapping (approximate):**
- Skill 5 ≈ 1200 ELO
- Skill 10 ≈ 1400 ELO  
- Skill 15 ≈ 1600 ELO
- Skill 18 ≈ 1800 ELO
- Skill 20 ≈ 2000+ ELO

#### 1.2 Position Selection Strategy
- **Early Positions**: Moves 4-6 (post-opening, pre-deep middlegame)
- **Late Positions**: Last 5-8 moves before game end (tactical phase)
- **Total Positions**: 10 games × 2 positions = 20 evaluation positions

#### 1.3 Storage Implementation
```python
import chess.engine
import chess
import chess.pgn
import json
import datetime
from pathlib import Path

def generate_and_store_game(skill_level, game_number, output_dir="chess_data"):
    """Generate a game and store as PGN file"""
    engine = chess.engine.SimpleEngine.popen_uci("stockfish")
    engine.configure({
        "Skill Level": skill_level
    })
    
    board = chess.Board()
    game = chess.pgn.Game()
    
    # Set metadata
    game.headers["White"] = f"Stockfish_Skill_{skill_level}"
    game.headers["Black"] = f"Stockfish_Skill_{skill_level}"
    game.headers["Date"] = datetime.datetime.now().strftime("%Y.%m.%d")
    game.headers["SkillLevel"] = str(skill_level)
    game.headers["TimeControl"] = "1s"
    
    node = game
    moves = []
    
    while not board.is_game_over():
        result = engine.play(board, chess.engine.Limit(time=1.0))
        board.push(result.move)
        moves.append(result.move)
        node = node.add_variation(result.move)
    
    game.headers["Result"] = board.result()
    engine.quit()
    
    # Save PGN file
    Path(f"{output_dir}/games").mkdir(parents=True, exist_ok=True)
    pgn_path = f"{output_dir}/games/skill_{skill_level}_game_{game_number}.pgn"
    
    with open(pgn_path, "w") as f:
        print(game, file=f)
    
    return moves, board.result(), pgn_path

def extract_test_positions(pgn_path, skill_level, game_number):
    """Extract test positions from a PGN file"""
    with open(pgn_path) as f:
        game = chess.pgn.read_game(f)
    
    board = chess.Board()
    positions = []
    moves = list(game.mainline_moves())
    
    for i, move in enumerate(moves):
        # Extract early (moves 3-5) and late (last 6 moves) positions
        if i in [3, 4, 5] or i >= len(moves) - 6:
            positions.append({
                'id': f"skill{skill_level}_g{game_number}_move{i+1}",
                'source_skill': skill_level,
                'estimated_elo': {5: 1200, 10: 1400, 15: 1600, 18: 1800, 20: 2000}[skill_level],
                'game_id': f"skill_{skill_level}_game_{game_number}",
                'move_number': i + 1,
                'phase': 'early' if i <= 5 else 'late',
                'fen': board.fen(),
                'best_move': move.uci(),
                'move_san': board.san(move),  # Standard algebraic notation
                'context': {
                    'total_moves': len(moves),
                    'game_result': game.headers.get("Result", "*")
                }
            })
        board.push(move)
    
    return positions

def create_complete_test_suite(output_dir="chess_data"):
    """Generate all games and create test suite"""
    skill_levels = [5, 10, 15, 18, 20]  # Approximate ELO: 1200, 1400, 1600, 1800, 2000+
    all_positions = []
    
    for skill in skill_levels:
        for game_num in range(1, 3):  # 2 games per skill level
            print(f"Generating Skill Level {skill}, Game {game_num}...")
            
            # Generate and store game
            moves, result, pgn_path = generate_and_store_game(skill, game_num, output_dir)
            
            # Extract positions
            positions = extract_test_positions(pgn_path, skill, game_num)
            all_positions.extend(positions)
    
    # Save test suite as JSON
    test_suite = {
        "metadata": {
            "version": "1.0",
            "generated_date": datetime.datetime.now().isoformat(),
            "total_positions": len(all_positions),
            "skill_levels": skill_levels,
            "elo_mapping": {5: 1200, 10: 1400, 15: 1600, 18: 1800, 20: 2000},
            "games_per_skill": 2
        },
        "positions": all_positions
    }
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    with open(f"{output_dir}/test_suite.json", "w") as f:
        json.dump(test_suite, f, indent=2)
    
    print(f"Generated {len(all_positions)} test positions")
    return f"{output_dir}/test_suite.json"
```

### Step 2: Move Grading System
Build logic to evaluate move quality using Stockfish analysis.

#### 2.1 Grading Algorithm
```python
class MoveGrader:
    def __init__(self, depth=15):
        self.engine = chess.engine.SimpleEngine.popen_uci("stockfish")
        self.depth = depth
    
    def grade_move(self, fen_before, move_played):
        board = chess.Board(fen_before)
        
        # Get current position evaluation
        info_before = self.engine.analyse(board, chess.engine.Limit(depth=self.depth))
        eval_before = info_before["score"].relative.score(mate_score=10000)
        
        # Get best moves for position
        multipv_info = self.engine.analyse(
            board, 
            chess.engine.Limit(depth=self.depth), 
            multipv=5
        )
        
        # Play the move
        board.push(chess.Move.from_uci(move_played))
        
        # Get evaluation after move
        info_after = self.engine.analyse(board, chess.engine.Limit(depth=self.depth))
        eval_after = -info_after["score"].relative.score(mate_score=10000)  # Flip perspective
        
        # Calculate evaluation drop
        eval_drop = eval_before - eval_after
        
        # Assign grade
        return self._classify_move(eval_drop, multipv_info, move_played)
    
    def _classify_move(self, eval_drop, best_moves, played_move):
        # Check if move was in top 5
        top_moves = [pv[0] for pv in best_moves]
        move_rank = top_moves.index(chess.Move.from_uci(played_move)) + 1 if chess.Move.from_uci(played_move) in top_moves else 6
        
        if eval_drop <= 10:  # Centipawn loss
            return {"grade": "Excellent", "eval_drop": eval_drop, "rank": move_rank}
        elif eval_drop <= 30:
            return {"grade": "Good", "eval_drop": eval_drop, "rank": move_rank}
        elif eval_drop <= 60:
            return {"grade": "Inaccuracy", "eval_drop": eval_drop, "rank": move_rank}
        elif eval_drop <= 100:
            return {"grade": "Mistake", "eval_drop": eval_drop, "rank": move_rank}
        else:
            return {"grade": "Blunder", "eval_drop": eval_drop, "rank": move_rank}
```

#### 2.2 Validation Tests
```python
def validate_grading_system():
    grader = MoveGrader()
    
    # Test 1: Known good vs bad moves
    test_cases = [
        {
            "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
            "good_move": "e5",    # Should grade well
            "bad_move": "a6"      # Should grade poorly
        }
    ]
    
    for case in test_cases:
        good_grade = grader.grade_move(case["fen"], case["good_move"])
        bad_grade = grader.grade_move(case["fen"], case["bad_move"])
        
        print(f"Good move ({case['good_move']}): {good_grade}")
        print(f"Bad move ({case['bad_move']}): {bad_grade}")
        
        assert good_grade["eval_drop"] < bad_grade["eval_drop"]
    
    # Test 2: ELO correlation
    # Higher ELO games should have better average grades
    
    print("Grading system validation passed!")
```

### Step 3: LLM Evaluation Pipeline
Create system to test LLMs and aggregate results.

#### 3.1 Test Suite Generation
```python
def create_test_suite():
    test_positions = []
    elo_levels = [1200, 1400, 1600, 1800, 2000]
    
    for elo in elo_levels:
        for game_num in range(2):  # 2 games per ELO
            moves, result = generate_game(elo)
            positions = extract_positions(moves)
            
            for pos in positions:
                test_positions.append({
                    **pos,
                    'source_elo': elo,
                    'game_id': f"{elo}_{game_num}",
                    'expected_grade': None  # Will be filled by grading actual move
                })
    
    # Save test suite
    import json
    with open('chess_test_suite.json', 'w') as f:
        json.dump(test_positions, f, indent=2)
    
    return test_positions
```

#### 3.2 LLM Evaluation
```python
class LLMChessEvaluator:
    def __init__(self, test_suite_path):
        self.grader = MoveGrader()
        with open(test_suite_path) as f:
            self.test_positions = json.load(f)
    
    def evaluate_llm(self, llm_move_function):
        results = []
        
        for position in self.test_positions:
            # Get LLM's move
            try:
                llm_move = llm_move_function(position['fen'])
                
                # Validate move is legal
                board = chess.Board(position['fen'])
                if chess.Move.from_uci(llm_move) not in board.legal_moves:
                    grade = {"grade": "Illegal", "eval_drop": float('inf')}
                else:
                    grade = self.grader.grade_move(position['fen'], llm_move)
                
                results.append({
                    **position,
                    'llm_move': llm_move,
                    'grade_info': grade
                })
                
            except Exception as e:
                results.append({
                    **position,
                    'llm_move': None,
                    'grade_info': {"grade": "Error", "error": str(e)}
                })
        
        return self._aggregate_results(results)
    
    def _aggregate_results(self, results):
        legal_moves = [r for r in results if r['grade_info']['grade'] != 'Illegal']
        
        if not legal_moves:
            return {"overall_score": 0, "legal_move_rate": 0}
        
        grade_scores = {"Excellent": 5, "Good": 4, "Inaccuracy": 3, "Mistake": 2, "Blunder": 1}
        total_score = sum(grade_scores.get(r['grade_info']['grade'], 0) for r in legal_moves)
        
        return {
            "overall_score": total_score / len(legal_moves),
            "legal_move_rate": len(legal_moves) / len(results),
            "grade_distribution": self._count_grades(legal_moves),
            "by_elo": self._analyze_by_elo(legal_moves),
            "by_phase": self._analyze_by_phase(legal_moves)
        }
```

## Implementation Timeline

### Phase 1: Core Infrastructure (Week 1)
- [ ] Set up Stockfish integration
- [ ] Implement game generation
- [ ] Create move grading system
- [ ] Validate grading with known positions

### Phase 2: Test Suite Creation (Week 1)
- [ ] Generate 10 games across ELO levels
- [ ] Extract and validate positions
- [ ] Create baseline grades for reference

### Phase 3: LLM Integration (Week 2)
- [ ] Build evaluation pipeline
- [ ] Test with sample LLM
- [ ] Refine scoring methodology
- [ ] Create reporting dashboard

## Success Metrics

### Validation Criteria
- Grading system correctly identifies obvious blunders
- Higher ELO games produce better average move grades
- System handles edge cases (illegal moves, timeouts)

### LLM Evaluation Metrics
- **Legal Move Rate**: % of moves that are legal
- **Average Move Quality**: Score from 1-5 based on grades
- **ELO Sensitivity**: Performance difference across position difficulties
- **Phase Analysis**: Early vs late game performance

## Extensions and Improvements

### Short Term
- Add opening book consultation
- Include tactical motif detection
- Test with puzzle positions

### Long Term
- Expand to different time controls
- Add positional concept evaluation
- Create ELO prediction model based on static evaluation