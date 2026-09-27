import Nav from "@/components/layout/Nav";
import Footer from "@/components/layout/Footer";
import ProgressChart from "@/components/dashboard/ProgressChart";

// Per ARCHITECTURE.md §4: "Visualize performance and progress."
export default function DashboardPage() {
  return (
    <>
      <div className="mx-auto max-w-none px-6 sm:px-14">
        <Nav />
      </div>

      <section className="py-14 pb-20">
        <div className="mx-auto max-w-3xl px-6 sm:px-14">
          <h1 className="font-display text-[clamp(30px,4vw,42px)] font-semibold">
            Your progress.
          </h1>
          <p className="mt-4 max-w-[55ch] text-[16px] opacity-80">
            Sample data shown below. Swap this for{" "}
            <code className="text-[14px]">GET /api/v1/performance</code>{" "}
            once the backend is live.
          </p>

          <div className="mt-10 rounded-[3px] border border-line bg-ink p-8">
            <ProgressChart />
          </div>
        </div>
      </section>

      <div className="mx-auto max-w-none px-6 sm:px-14">
        <Footer />
      </div>
    </>
  );
}
