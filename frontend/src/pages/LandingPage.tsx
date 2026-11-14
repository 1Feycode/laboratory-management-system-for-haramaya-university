import { Link } from "react-router-dom";

const features = [
  {
    number: "01",
    title: "Laboratory asset inventory",
    description:
      "Search and filter registered equipment, then review its asset passport, current status, and recorded location.",
  },
  {
    number: "02",
    title: "Asset registration and identification",
    description:
      "Authorized users can register equipment with a generated asset code and QR-based identification.",
  },
  {
    number: "03",
    title: "Asset assignment and transfer",
    description:
      "Track custody changes through the transfer workflow while preserving source and destination history.",
  },
  {
    number: "04",
    title: "Maintenance and repair tracking",
    description:
      "Report faults, follow work orders, record repair activities, and retain maintenance history.",
  },
  {
    number: "05",
    title: "Calibration records and due dates",
    description:
      "Record calibration results and review equipment with upcoming or overdue calibration dates.",
  },
  {
    number: "06",
    title: "Audit trail and accountability",
    description:
      "Key asset and workflow changes are retained in append-only audit records.",
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-5 py-4 sm:px-8">
          <div className="flex min-w-0 items-center gap-3">
            <Link
              to="/"
              className="shrink-0 rounded-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-university-700"
              aria-label="Haramaya University Laboratory Asset Management home"
            >
              <img
                src="/assets/haramaya-university-logo.png"
                alt="Haramaya University"
                className="h-7 w-auto max-w-[145px] object-contain sm:h-9 sm:max-w-[190px]"
              />
            </Link>
            <span className="hidden max-w-44 border-l border-slate-200 pl-3 text-xs font-medium leading-5 text-slate-600 sm:block">
              Laboratory Asset Management
            </span>
          </div>

          <nav
            aria-label="Main navigation"
            className="flex items-center gap-3 text-sm sm:gap-6"
          >
            <a
              href="#features"
              className="hidden rounded-sm text-slate-700 hover:text-university-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-university-700 sm:inline"
            >
              Features
            </a>
            <a
              href="#overview"
              className="hidden rounded-sm text-slate-700 hover:text-university-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-university-700 sm:inline"
            >
              About the system
            </a>
            <Link
              to="/login"
              className="inline-flex min-h-11 items-center justify-center rounded-lg border border-university-700 bg-university-700 px-4 font-semibold text-white transition-colors hover:bg-university-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-university-700"
            >
              Sign in
            </Link>
          </nav>
        </div>
      </header>

      <main>
        <section className="relative isolate overflow-hidden border-b border-slate-200 bg-slate-950">
          <img
            src="/assets/haramaya-campus-background.jpg"
            alt="Aerial view of Haramaya University’s main campus buildings and surrounding landscape"
            className="absolute inset-0 h-full w-full object-cover object-center"
            decoding="async"
          />
          <div
            aria-hidden="true"
            className="pointer-events-none absolute inset-0 bg-gradient-to-r from-university-950/90 via-university-900/80 to-university-800/65"
          />
          <div className="relative mx-auto grid max-w-7xl items-center gap-12 px-5 py-16 sm:px-8 sm:py-24 lg:grid-cols-[1.1fr_0.9fr] lg:gap-16 lg:py-28">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border-l-4 border-university-orange-500 border-y border-r border-white/30 bg-white/10 px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.14em] text-white">
                Laboratory operations
              </p>
              <h1 className="mt-6 max-w-3xl text-4xl font-semibold leading-tight tracking-tight text-white sm:text-5xl lg:text-6xl">
                Laboratory Asset Management and Maintenance Tracking System
              </h1>
              <p className="mt-6 max-w-2xl text-lg leading-8 text-white/90">
                An integrated platform for managing laboratory assets, tracking
                maintenance activities, and monitoring calibration records at
                Haramaya University.
              </p>
              <div className="mt-8 flex flex-wrap items-center gap-4">
                <Link
                  to="/login"
                  className="inline-flex min-h-12 items-center justify-center rounded-lg bg-white px-6 font-semibold text-university-900 shadow-sm transition-colors hover:bg-university-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
                >
                  Sign in to the system
                </Link>
                <a
                  href="#features"
                  className="inline-flex min-h-12 items-center rounded-lg px-4 font-semibold text-white underline decoration-white/60 underline-offset-4 hover:text-university-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
                >
                  Explore features
                </a>
              </div>
            </div>

            <section
              aria-labelledby="landing-overview-title"
              className="rounded-3xl border border-slate-200 bg-slate-50 p-5 shadow-xl shadow-slate-200/60 sm:p-8"
            >
              <div className="rounded-2xl border border-slate-200 bg-white p-5 sm:p-7">
                <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
                  System overview
                </p>
                <h2 className="mt-2 text-xl font-semibold text-slate-900">
                  <span id="landing-overview-title">
                    Connected equipment records
                  </span>
                </h2>
                <p className="mt-2 text-sm leading-6 text-slate-600">
                  A shared view of an asset’s lifecycle information.
                </p>

                <div className="mt-6 space-y-3">
                  {[
                    ["Asset inventory", "Identification and current location"],
                    ["Maintenance", "Fault reports and repair history"],
                    ["Calibration", "Recorded results and due dates"],
                  ].map(([title, detail], index) => (
                    <div
                      key={title}
                      className="flex items-center gap-4 rounded-xl border border-slate-200 bg-white p-4"
                    >
                      <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-university-100 text-sm font-semibold text-university-800">
                        0{index + 1}
                      </span>
                      <div>
                        <p className="font-semibold text-slate-900">{title}</p>
                        <p className="mt-0.5 text-sm text-slate-600">{detail}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <p className="mt-4 text-center text-xs text-slate-500">
                An overview of supported system areas — not live application data
              </p>
            </section>
          </div>
        </section>

        <section id="features" className="scroll-mt-8 py-16 sm:py-20">
          <div className="mx-auto max-w-7xl px-5 sm:px-8">
            <div className="max-w-2xl">
              <p className="text-sm font-semibold uppercase tracking-[0.14em] text-university-700">
                System capabilities
              </p>
              <h2 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950 sm:text-4xl">
                Practical tools for laboratory equipment
              </h2>
              <p className="mt-4 leading-7 text-slate-600">
                The application brings together the records and workflows
                currently available to authorized users.
              </p>
            </div>

            <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {features.map((feature) => (
                <article
                  key={feature.number}
                  className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition-shadow hover:shadow-md"
                >
                  <span className="inline-flex h-9 min-w-9 items-center justify-center rounded-lg bg-university-50 px-2 text-sm font-semibold text-university-800">
                    {feature.number}
                  </span>
                  <h3 className="mt-5 text-lg font-semibold text-slate-900">
                    {feature.title}
                  </h3>
                  <p className="mt-2 leading-6 text-slate-600">
                    {feature.description}
                  </p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section id="overview" className="scroll-mt-8 border-y border-slate-200 bg-white py-16 sm:py-20">
          <div className="mx-auto grid max-w-7xl gap-8 px-5 sm:px-8 lg:grid-cols-[0.8fr_1.2fr] lg:gap-16">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.14em] text-slate-600">
                About the system
              </p>
              <h2 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950">
                One place for essential equipment records
              </h2>
            </div>
            <div className="space-y-4 leading-7 text-slate-600">
              <p>
                The system supports laboratory asset registration and
                identification, custody transfer history, maintenance work
                orders, and calibration records.
              </p>
              <p>
                Access to application features is based on the user’s assigned
                system role. The platform presents recorded information to
                support asset oversight and maintenance activities; it does not
                replace institutional approval or procurement processes.
              </p>
              <p>
                Preventive maintenance scheduling is not currently provided.
              </p>
            </div>
          </div>
        </section>

        <section className="bg-university-950 py-14 text-white sm:py-16">
          <div className="mx-auto flex max-w-7xl flex-col items-start justify-between gap-6 px-5 sm:px-8 md:flex-row md:items-center">
            <div>
              <h2 className="text-2xl font-semibold tracking-tight">
                Access the laboratory asset system
              </h2>
              <p className="mt-2 max-w-2xl leading-7 text-white/80">
                Sign in with an account provisioned by a ULMD administrator.
              </p>
            </div>
            <Link
              to="/login"
              className="inline-flex min-h-12 shrink-0 items-center justify-center rounded-lg bg-white px-6 font-semibold text-university-900 transition-colors hover:bg-university-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
            >
              Sign in
            </Link>
          </div>
        </section>
      </main>

      <footer className="bg-slate-950 text-slate-300">
        <div className="mx-auto flex max-w-7xl flex-col gap-6 px-5 py-10 sm:px-8 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="font-semibold text-white">Haramaya University</p>
            <p className="mt-1 text-sm font-medium text-slate-200">
              Laboratory Asset Management and Maintenance Tracking System
            </p>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
              A platform for managing laboratory asset records, maintenance
              activities, and calibration information.
            </p>
          </div>
          <p className="text-sm text-slate-400">
            © {new Date().getFullYear()} Haramaya University
          </p>
        </div>
      </footer>
    </div>
  );
}
