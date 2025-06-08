import { createAsync } from "@solidjs/router";
import { query } from "@solidjs/router";
import { db } from "~/lib/db";

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

export default function Home() {
  const evalData = createAsync(() => getEvalData());

  return (
    <main class="text-center mx-auto text-gray-700 p-4 max-w-4xl">
      <div class="mt-8">
        <h2 class="text-2xl font-bold mb-4">Evaluation Results</h2>
        <div class="bg-white p-4 rounded-lg">
          <pre class="text-left text-sm overflow-auto max-h-96">
            {JSON.stringify(evalData(), null, 2)}
          </pre>
        </div>
      </div>
    </main>
  );
}
