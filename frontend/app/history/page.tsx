import Nav from "@/components/layout/Nav";
import Footer from "@/components/layout/Footer";

// Per ARCHITECTURE.md §4: "Show past interactions."
// Wire this up to lib/api.ts's getHistory() once GET /api/v1/history exists.
export default function HistoryPage() {
  return (
    <>
      <div className="mx-auto max-w-none px-6 sm:px-14">
        <Nav />
      </div>

      <section className="py-14 pb-20">
        <div className="mx-auto max-w-3xl px-6 sm:px-14">
          <h1 className="font-display text-[clamp(30px,4vw,42px)] font-semibold">
            Your past rounds.
          </h1>
          <p className="mt-4 max-w-[55ch] text-[16px] opacity-80">
            Every submission you&rsquo;ve sent through Penfight will show up
            here, paginated and searchable, once{" "}
            <code className="text-[14px]">GET /api/v1/history</code> is live.
          </p>

          <div className="mt-10 rounded-[3px] border border-line bg-[#FBF7EC] p-8 text-center text-[15px] opacity-60">
            No history yet — your first submission will appear here.
          </div>
        </div>
      </section>

      <div className="mx-auto max-w-none px-6 sm:px-14">
        <Footer />
      </div>
    </>
  );
}
