import Nav from "@/components/layout/Nav";
import Footer from "@/components/layout/Footer";
import MarkupDemo from "@/components/input/MarkupDemo";
import HowItWorks from "@/components/analysis/HowItWorks";
import Capabilities from "@/components/analysis/Capabilities";
import ProgressSection from "@/components/dashboard/ProgressSection";

export default function HomePage() {
  return (
    <>
      <div className="mx-auto max-w-none px-6 sm:px-14">
        <Nav />
      </div>

      <section className="py-9 pb-20">
        <div className="mx-auto grid max-w-none grid-cols-1 items-center gap-12 px-6 sm:px-14 lg:grid-cols-[1.05fr_1fr] lg:gap-16">
          <div>
            <h1 className="font-display text-[clamp(38px,5vw,58px)] font-semibold leading-[1.06]">
              Every draft
              <br />
              deserves a
              <br />
              second read.
            </h1>
            <p className="mt-[22px] max-w-[44ch] text-[19px] opacity-80">
              Paste anything you&rsquo;ve written — an essay, a pitch, a report.
              Penfight reads it the way a sharp editor would, then remembers
              what you kept getting wrong last time.
            </p>
            <div className="mt-[34px] flex flex-wrap items-center gap-4">
              <button className="rounded-sm bg-burgundy px-6 py-[14px] text-[15.5px] font-medium text-paper">
                Get your first read
              </button>
              <button className="rounded-sm border border-[#201C14] px-[22px] py-[13px] text-[15.5px]">
                See a sample
              </button>
            </div>
          </div>

          <MarkupDemo />
        </div>
      </section>

      <HowItWorks />
      <Capabilities />
      <ProgressSection />

      <section className="py-[90px]">
        <div className="mx-auto max-w-none px-6 sm:px-14">
          <h2 className="max-w-[16ch] font-display text-[clamp(32px,4vw,46px)] font-semibold">
            Send it your next draft.
          </h2>
          <button className="mt-[26px] rounded-sm bg-burgundy px-6 py-[14px] text-[15.5px] font-medium text-paper">
            Start your first round
          </button>
        </div>
      </section>

      <div className="mx-auto max-w-none px-6 sm:px-14">
        <Footer />
      </div>
    </>
  );
}
