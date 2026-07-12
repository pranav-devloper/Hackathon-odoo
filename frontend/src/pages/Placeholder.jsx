import DashLayout from "../components/DashLayout";

// Generic placeholder for sections without a backend yet (Bookings, Maintenance,
// Reports, Settings). Uses the shared shell so navigation stays consistent.
export default function Placeholder({ title }) {
  return (
    <DashLayout>
      <h1>{title}</h1>
      <section className="panel placeholder-panel">
        <p className="muted">
          The <strong>{title}</strong> section is a placeholder. The backend
          currently provides authentication only — once {title.toLowerCase()}{" "}
          endpoints exist, this page will list and manage that data.
        </p>
      </section>
    </DashLayout>
  );
}
