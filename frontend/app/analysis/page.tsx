import Nav from "@/components/layout/Nav";
import Footer from "@/components/layout/Footer";
import MarkupDemo from "@/components/input/MarkupDemo";

// Per ARCHITECTURE.md §4: "Accept input, show live analysis."
// The heuristic demo stands in for a real POST /api/v1/analyze call
// (see lib/api.ts) until the backend is wired up.
export default function AnalysisPage() {
  return (
    <>
      <div className="mx-auto max-w-none px-6 sm:px-14">
        <Nav />
      </div>

      <section className="py-14 pb-20">
        <div className="mx-auto max-w-2xl px-6 sm:px-14">
          <h1 className="font-display text-[clamp(30px,4vw,42px)] font-semibold">
            Submit something for a read.
          </h1>
          <p className="mt-4 max-w-[50ch] text-[16px] opacity-80">
            Paste your draft below. Once the backend is connected, this will
            call <code className="text-[14px]">POST /api/v1/analyze</code> and
            show structured feedback instead of the local heuristic preview.
          </p>

          <div className="mt-10">
            <MarkupDemo />
          </div>
        </div>
      </section>

      <div className="mx-auto max-w-none px-6 sm:px-14">
        <Footer />
      </div>
    </>
  );
}
