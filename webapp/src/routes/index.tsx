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

const getEvalData = query(async () => {
  "use server";
  try {
    const results = await db.selectFrom("evalresult").selectAll().execute();

    console.log(results);
    return results;
  } catch (error) {
    console.error("Error fetching eval data:", error);
    return [];
  }
}, "eval-data");

// Formatting utilities
const formatScore = (score: number) => score.toFixed(4);
const formatTimestamp = (date: Date) => new Date(date).toLocaleString();
const formatRuns = (runs: number | null) => runs || "N/A";

// CSS classes organization
const tableStyles = {
  container: "bg-white p-4 rounded-lg shadow-lg overflow-x-auto",
  table: "w-full border-collapse",
  headerRow: "border-b-2 border-gray-200",
  headerCell: "text-left p-3 font-semibold text-gray-700 bg-gray-50",
  sortableHeader:
    "cursor-pointer select-none hover:bg-gray-100 p-2 rounded flex items-center gap-2",
  nonSortableHeader: "p-2",
  sortIndicator: "text-xs",
  bodyRow: "border-b border-gray-100 hover:bg-gray-50",
  bodyCell: "p-3 text-sm",
  footer: "mt-4 text-sm text-gray-600 flex justify-between items-center",
  sortStatus: "text-xs",
  sortBadge: "ml-1 bg-blue-100 text-blue-800 px-2 py-1 rounded",
  emptyState: "text-gray-500 py-8",
};

// Column definitions
const createEvalColumns = (): ColumnDef<Selectable<Evalresult>>[] => [
  {
    accessorKey: "model_name",
    header: "Model Name",
    cell: (info) => info.getValue(),
  },
  {
    accessorKey: "eval_name",
    header: "Evaluation",
    cell: (info) => info.getValue(),
  },
  {
    accessorKey: "result",
    header: "Score",
    cell: (info) => {
      const value = info.getValue() as number;
      return formatScore(value);
    },
  },
  {
    accessorKey: "runs",
    header: "Runs",
    cell: (info) => formatRuns(info.getValue() as number | null),
  },
  {
    accessorKey: "timestamp",
    header: "Timestamp",
    cell: (info) => {
      const value = info.getValue() as Date;
      return formatTimestamp(value);
    },
  },
];

export default function Home() {
  const evalData = createAsync(() => getEvalData());
  const [sorting, setSorting] = createSignal<SortingState>([]);

  const columns = createEvalColumns();

  const table = createSolidTable({
    get data() {
      const data = evalData();
      return data || [];
    },
    columns,
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
        <h2 class="text-2xl font-bold mb-4">Evaluation Results</h2>
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
              <span>{table.getRowModel().rows.length} Results</span>
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
