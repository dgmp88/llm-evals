import { A } from "@solidjs/router";
import { createAsync } from "@solidjs/router";
import { action, cache } from "@solidjs/router";
import { db } from "~/lib/db";

const getEvalData = cache(async () => {
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
      <h1 class="max-6-xs text-6xl text-sky-700 font-thin uppercase my-16">
        LLM Evals Dashboard
      </h1>

      <div class="mt-8">
        <h2 class="text-2xl font-bold mb-4">Evaluation Results</h2>
        <div class="bg-gray-100 p-4 rounded-lg">
          <pre class="text-left text-sm overflow-auto max-h-96">
            {JSON.stringify(evalData(), null, 2)}
          </pre>
        </div>
      </div>

      <p class="mt-8">
        Visit{" "}
        <a
          href="https://solidjs.com"
          target="_blank"
          class="text-sky-600 hover:underline"
        >
          solidjs.com
        </a>{" "}
        to learn how to build Solid apps.
      </p>
      <p class="my-4">
        <span>Home</span>
        {" - "}
        <A href="/about" class="text-sky-600 hover:underline">
          About Page
        </A>{" "}
      </p>
    </main>
  );
}
