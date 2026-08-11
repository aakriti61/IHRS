export default function PatientInfoCard({ patient }) {
  if (!patient) return null;

  const fields = [
    { label: "Phone", value: patient.phone },
    { label: "Blood group", value: patient.blood_group },
    { label: "Date of birth", value: patient.dob },
    { label: "Emergency contact", value: patient.emergency_contact },
  ];

  return (
    <div className="card border-gold/40 bg-gold-light/30">
      <div className="flex items-center justify-between">
        <h2 className="font-display text-lg font-medium text-ink">{patient.full_name}</h2>
        <span className="font-mono text-xs text-ink/50">{patient.nhid}</span>
      </div>
      <div className="mt-3 grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
        {fields.map((f) => (
          <div key={f.label}>
            <p className="text-xs uppercase tracking-wide text-ink/40">{f.label}</p>
            <p className="mt-0.5 font-medium text-ink">{f.value || "--"}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
