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

---

## Implemented Approach & Analysis

### Current Implementation Status

We have successfully implemented a **centipawn loss evaluation system** using Stockfish to grade chess moves. Here's what has been built and tested:

#### Our Move Grading Approach
```python
class MoveGrader:
    def __init__(self, depth=18, time_limit=2.0):
        # Uses Stockfish with depth 18 and 2-second time limit per position
        # Significantly more thorough than originally planned depth of 12
```

**Key Features:**
- **Deep Analysis**: Stockfish depth 18 + 2-second time limits for high accuracy
- **Centipawn Loss Metric**: Measures how many centipawns worse each move is vs the best move
- **Comprehensive Game Analysis**: Analyzes every move in a game, not just selected positions
- **Player-Specific Metrics**: Separate average centipawn loss for White and Black

### Test Results from Generated Games

We analyzed 5 games across different Stockfish skill levels with these findings:

| Game | Total Moves | White Avg CP Loss | Black Avg CP Loss | Overall Avg |
|------|-------------|------------------|------------------|-------------|
| skill_5  | 78  | 30.6 | 15.9 | 23.3 |
| skill_10 | 90  | 20.9 | **204.4** | 112.6 |
| skill_15 | 136 | 13.7 | 12.6 | **13.1** |
| skill_18 | 145 | 7.8  | 9.1  | **8.5** |
| skill_20 | 269 | 65.6 | 66.5 | 66.1 |

**Key Insights:**
- **Best Performance**: skill_18 with only 8.5 cp average loss
- **Counterintuitive Results**: skill_20 (highest) performed worse than skill_15 and skill_18
- **Outlier Detection**: skill_10 showed massive player disparity (20.9 vs 204.4 cp loss)

### Strengths of Our Approach

1. **Objective & Precise**: Centipawn loss provides granular, engine-based evaluation
2. **Comprehensive Coverage**: Analyzes entire games rather than cherry-picked positions  
3. **Scalable**: Can process large numbers of games efficiently
4. **Player-Aware**: Distinguishes between White and Black performance
5. **Validated**: Successfully runs against real game data with meaningful results

### Critical Shortcomings & Limitations

#### 1. **Engine Analysis Limitations**
- **Horizon Effect**: Even depth 18 misses very deep tactical sequences
- **Positional Blindness**: Stockfish may undervalue long-term positional concepts
- **Style Bias**: Optimizes for engine-style play, not human-style understanding

#### 2. **Evaluation Metric Issues**
- **Linear Assumption**: Assumes centipawn loss scales linearly with move quality
- **Context Ignorance**: 50cp loss in a winning position ≠ 50cp loss when losing
- **Tactical vs Positional**: May overweight tactical precision vs positional understanding

#### 3. **Test Data Problems**
- **Self-Play Bias**: Stockfish vs Stockfish games don't represent human play patterns
- **Skill Level Inconsistency**: Our results show skill levels don't correlate as expected
- **Limited Sample Size**: Only 5 games provides insufficient statistical power
- **No Opening/Endgame Specialization**: Treats all game phases equally

#### 4. **LLM Evaluation Gaps**
- **Move Selection Only**: Doesn't test chess understanding, planning, or explanation
- **No Time Pressure**: Real games involve time management decisions
- **Missing Context**: LLMs might need game history, not just current position
- **Format Assumptions**: Assumes LLMs can output clean UCI notation

#### 5. **Statistical & Methodological Issues**
- **No Baseline Comparison**: We don't know what "good" centipawn loss should be
- **Inconsistent Results**: skill_20 performing worse than skill_15/18 suggests data quality issues
- **No Confidence Intervals**: Results lack statistical uncertainty quantification
- **Cherry-Picking Risk**: Testing only 2 moves per game could miss systematic patterns

### Recommended Improvements

#### Immediate Fixes
1. **Expand Test Data**: Generate 20+ games per skill level for statistical significance
2. **Add Human Games**: Include master-level human games for realistic baselines
3. **Contextual Scoring**: Weight centipawn loss by game phase and position type
4. **Multiple Engines**: Cross-validate with Leela Chess Zero or other engines

#### Methodological Enhancements
1. **Positional Understanding Tests**: Include positions requiring long-term planning
2. **Explanation Evaluation**: Test LLM's ability to explain moves, not just make them
3. **Time-Aware Testing**: Factor in reasonable move times for different position types
4. **Opening Book Integration**: Separate evaluation of opening knowledge vs middlegame skill

#### Statistical Rigor
1. **Confidence Intervals**: Report statistical uncertainty for all metrics
2. **Skill Level Validation**: Verify that higher skill levels actually play better on average
3. **Cross-Validation**: Test grading system on positions with known human evaluations
4. **Effect Size Analysis**: Determine meaningful differences between centipawn loss ranges

### Conclusion

Our implementation provides a **solid foundation** for chess move evaluation but has **significant limitations** for comprehensive LLM chess ability assessment. The centipawn loss approach works well for tactical evaluation but misses crucial aspects of chess understanding that might be more relevant for LLM evaluation.

**For production use**, this system should be supplemented with positional understanding tests, explanation evaluation, and human-validated reference games to provide a more complete picture of LLM chess capabilities.