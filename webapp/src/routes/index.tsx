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

interface EvalResult {
  id: number;
  model_name: string;
  eval_name: string;
  result: number;
  runs: number | null;
  timestamp: Date;
}

export default function Home() {
  const evalData = createAsync(() => getEvalData());
  const [sorting, setSorting] = createSignal<SortingState>([]);

  const columns: ColumnDef<EvalResult>[] = [
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
        return value.toFixed(4);
      },
    },
    {
      accessorKey: "runs",
      header: "Runs",
      cell: (info) => info.getValue() || "N/A",
    },
    {
      accessorKey: "timestamp",
      header: "Timestamp",
      cell: (info) => {
        const value = info.getValue() as Date;
        return new Date(value).toLocaleString();
      },
    },
  ];

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
        <div class="bg-white p-4 rounded-lg shadow-lg overflow-x-auto">
          <Show
            when={(evalData()?.length ?? 0) > 0}
            fallback={
              <div class="text-gray-500 py-8">No evaluation results found</div>
            }
          >
            <table class="w-full border-collapse">
              <thead>
                <For each={table.getHeaderGroups()}>
                  {(headerGroup) => (
                    <tr class="border-b-2 border-gray-200">
                      <For each={headerGroup.headers}>
                        {(header) => (
                          <th class="text-left p-3 font-semibold text-gray-700 bg-gray-50">
                            <Show when={!header.isPlaceholder}>
                              <div
                                class={
                                  header.column.getCanSort()
                                    ? "cursor-pointer select-none hover:bg-gray-100 p-2 rounded flex items-center gap-2"
                                    : "p-2"
                                }
                                onClick={header.column.getToggleSortingHandler()}
                              >
                                {flexRender(
                                  header.column.columnDef.header,
                                  header.getContext(),
                                )}
                                <span class="text-xs">
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
                    <tr class="border-b border-gray-100 hover:bg-gray-50">
                      <For each={row.getVisibleCells()}>
                        {(cell) => (
                          <td class="p-3 text-sm">
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
            <div class="mt-4 text-sm text-gray-600 flex justify-between items-center">
              <span>{table.getRowModel().rows.length} Results</span>
              <Show when={sorting().length > 0}>
                <div class="text-xs">
                  <span class="font-medium">Sorted by:</span>
                  <For each={sorting()}>
                    {(sort) => (
                      <span class="ml-1 bg-blue-100 text-blue-800 px-2 py-1 rounded">
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
