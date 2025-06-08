import { createAsync } from "@solidjs/router";
import { query } from "@solidjs/router";
import { db } from "~/lib/db";
import {
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  SortingState,
  ColumnDef,
  createSolidTable,
} from "@tanstack/solid-table";
import { createSignal, For, Show } from "solid-js";
import type { Selectable } from "kysely";
import type { Evalresult } from "~/lib/db.d";

// Types for pivoted data
interface PivotedRow {
  provider: string;
  model: string;
  [evalName: string]: string | { score: number; timestamp: Date };
}

const getEvalData = query(async () => {
  "use server";
  try {
    // Get all results first, then deduplicate in JavaScript to get the latest
    const allResults = await db.selectFrom("evalresult").selectAll().execute();

    console.log("Raw results:", allResults);

    // Group by provider/model and eval_name, keeping only the latest timestamp for each combination
    const latestResults = new Map<string, Selectable<Evalresult>>();

    allResults.forEach((result) => {
      const key = `${result.provider}/${result.model}-${result.eval_name}`;
      const existing = latestResults.get(key);

      if (
        !existing ||
        new Date(result.timestamp) > new Date(existing.timestamp)
      ) {
        latestResults.set(key, result);
      }
    });

    const results = Array.from(latestResults.values());

    // Transform data into pivoted structure
    const pivotedData: PivotedRow[] = [];
    const modelMap = new Map<string, PivotedRow>();

    // Group by model and create pivoted rows
    results.forEach((result) => {
      const modelKey = `${result.provider}/${result.model}`;
      if (!modelMap.has(modelKey)) {
        modelMap.set(modelKey, {
          provider: result.provider,
          model: result.model,
        });
      }

      const row = modelMap.get(modelKey)!;
      row[result.eval_name] = {
        score: result.result,
        timestamp: result.timestamp,
      };
    });

    const finalData = Array.from(modelMap.values());
    console.log("Pivoted data:", finalData);
    return finalData;
  } catch (error) {
    console.error("Error fetching eval data:", error);
    return [];
  }
}, "eval-data");

// Formatting utilities
const formatScore = (score: number) => score.toFixed(2);
const formatTimestamp = (date: Date) => new Date(date).toLocaleString();

// Function to calculate background color based on score (0-1 range)
const getScoreBackgroundColor = (score: number): string => {
  // Clamp score between 0 and 1
  const clampedScore = Math.max(0, Math.min(1, score));

  if (clampedScore <= 0.5) {
    // From red (0) to transparent (0.5)
    const intensity = (0.5 - clampedScore) / 0.5; // 1 at score=0, 0 at score=0.5
    const opacity = Math.round(intensity * 50); // Max 50% opacity
    return `rgba(239, 68, 68, ${opacity / 100})`; // red-500 with calculated opacity
  } else {
    // From transparent (0.5) to green (1)
    const intensity = (clampedScore - 0.5) / 0.5; // 0 at score=0.5, 1 at score=1
    const opacity = Math.round(intensity * 50); // Max 50% opacity
    return `rgba(34, 197, 94, ${opacity / 100})`; // green-500 with calculated opacity
  }
};

// Evaluation explanations mapping
const evalExplanations: Record<string, string> = {
  math_eval:
    "Fraction correct of 50 x 3 digit multiplication/division/addition/subtraction problems <br><br> e.g. 394*123",
  tictactoe_random:
    "Average win rate of 10 x full games of tic tac toe against an opponent playing randomly <br><br> 0 for loss, 0.5 for draw, 1 for win",
  tictactoe_perfect:
    "Average win rate of 10 x full games of tic tac toe against an opponent playing perfectly <br><br> 0 for loss, 0.5 for draw, 1 for win",
};

const getEvalExplanation = (evalName: string): string => {
  for (const [key, explanation] of Object.entries(evalExplanations)) {
    if (evalName.includes(key)) {
      return explanation;
    }
  }
  return `${evalName} evaluation - No detailed description available`;
};

// CSS classes organization
const tableStyles = {
  container: "bg-white p-4 rounded-lg shadow-lg overflow-x-auto relative",
  table: "w-full border-collapse",
  headerRow: "border-b-2 border-gray-200",
  headerCell:
    "text-left p-3 font-semibold text-gray-700 bg-gray-50 relative overflow-visible",
  sortableHeader:
    "cursor-pointer select-none hover:bg-gray-100 p-2 rounded flex items-center gap-2",
  nonSortableHeader: "p-2",
  sortIndicator: "text-xs",
  bodyRow: "border-b border-gray-100 hover:bg-gray-50",
  bodyCell: "p-3 text-sm relative",
  footer: "mt-4 text-sm text-gray-600 flex justify-between items-center",
  sortStatus: "text-xs",
  sortBadge: "ml-1 bg-blue-100 text-blue-800 px-2 py-1 rounded",
  emptyState: "text-gray-500 py-8",
  scoreCell:
    "cursor-help hover:bg-blue-50 transition-colors duration-200 relative group",
  tooltip:
    "absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-10",
  evalHeader: "relative group cursor-help",
  evalTooltip:
    "fixed px-3 py-2 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-normal max-w-xs z-50 text-center transform -translate-x-1/2",
  helpIcon: "text-gray-400 text-xs ml-1",
};

// Create dynamic columns based on unique evaluations
const createDynamicColumns = (data: PivotedRow[]): ColumnDef<PivotedRow>[] => {
  if (!data || data.length === 0) return [];

  // Get all unique evaluation names
  const evalNames = new Set<string>();
  data.forEach((row) => {
    Object.keys(row).forEach((key) => {
      if (key !== "provider" && key !== "model") {
        evalNames.add(key);
      }
    });
  });

  const columns: ColumnDef<PivotedRow>[] = [
    {
      accessorKey: "provider",
      header: "Provider",
      cell: (info) => info.getValue() as string,
    },
    {
      accessorKey: "model",
      header: "Model",
      cell: (info) => info.getValue() as string,
    },
  ];

  // Add a column for each evaluation
  Array.from(evalNames)
    .sort()
    .forEach((evalName) => {
      columns.push({
        accessorKey: evalName,
        header: () => (
          <div class={tableStyles.evalHeader}>
            <span>{evalName}</span>
            <span class={tableStyles.helpIcon}>❓</span>
            <div
              class={tableStyles.evalTooltip}
              innerHTML={getEvalExplanation(evalName)}
            ></div>
          </div>
        ),
        accessorFn: (row) => {
          const value = row[evalName] as
            | { score: number; timestamp: Date }
            | undefined;
          return value?.score; // Return just the score for sorting, undefined for missing values
        },
        cell: (info) => {
          const value = info.row.original[evalName] as
            | { score: number; timestamp: Date }
            | undefined;
          if (!value) return "-";

          return (
            <div
              class={tableStyles.scoreCell}
              style={{
                "background-color": getScoreBackgroundColor(value.score),
              }}
            >
              {formatScore(value.score)}
              <div class={tableStyles.tooltip}>
                {formatTimestamp(value.timestamp)}
              </div>
            </div>
          );
        },
        sortUndefined: "last",
      });
    });

  return columns;
};

export default function Home() {
  const evalData = createAsync(() => getEvalData());
  const [sorting, setSorting] = createSignal<SortingState>([]);

  const table = createSolidTable({
    get data() {
      const data = evalData();
      return data || [];
    },
    get columns() {
      const data = evalData();
      return createDynamicColumns(data || []);
    },
    state: {
      get sorting() {
        return sorting();
      },
    },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  return (
    <main class="text-center mx-auto text-gray-700 p-4 max-w-6xl">
      <div class="mt-8">
        <h2 class="text-2xl font-bold mb-4">Results</h2>
        <p>
          Hover over column titles for info on scores. All scores 0-1, 0 is
          worst, 1 is best.
        </p>
        <div class={tableStyles.container}>
          <Show
            when={(evalData()?.length ?? 0) > 0}
            fallback={
              <div class={tableStyles.emptyState}>
                No evaluation results found
              </div>
            }
          >
            <table class={tableStyles.table}>
              <thead>
                <For each={table.getHeaderGroups()}>
                  {(headerGroup) => (
                    <tr class={tableStyles.headerRow}>
                      <For each={headerGroup.headers}>
                        {(header) => (
                          <th class={tableStyles.headerCell}>
                            <Show when={!header.isPlaceholder}>
                              <div
                                class={
                                  header.column.getCanSort()
                                    ? tableStyles.sortableHeader
                                    : tableStyles.nonSortableHeader
                                }
                                onClick={header.column.getToggleSortingHandler()}
                              >
                                {flexRender(
                                  header.column.columnDef.header,
                                  header.getContext(),
                                )}
                                <span class={tableStyles.sortIndicator}>
                                  {{
                                    asc: "🔼",
                                    desc: "🔽",
                                  }[header.column.getIsSorted() as string] ??
                                    "↕️"}
                                </span>
                              </div>
                            </Show>
                          </th>
                        )}
                      </For>
                    </tr>
                  )}
                </For>
              </thead>
              <tbody>
                <For each={table.getRowModel().rows}>
                  {(row) => (
                    <tr class={tableStyles.bodyRow}>
                      <For each={row.getVisibleCells()}>
                        {(cell) => (
                          <td class={tableStyles.bodyCell}>
                            {flexRender(
                              cell.column.columnDef.cell,
                              cell.getContext(),
                            )}
                          </td>
                        )}
                      </For>
                    </tr>
                  )}
                </For>
              </tbody>
            </table>
            <div class={tableStyles.footer}>
              <span>{table.getRowModel().rows.length} Models</span>
              <Show when={sorting().length > 0}>
                <div class={tableStyles.sortStatus}>
                  <span class="font-medium">Sorted by:</span>
                  <For each={sorting()}>
                    {(sort) => (
                      <span class={tableStyles.sortBadge}>
                        {sort.id} ({sort.desc ? "desc" : "asc"})
                      </span>
                    )}
                  </For>
                </div>
              </Show>
            </div>
          </Show>
        </div>
      </div>
    </main>
  );
}
