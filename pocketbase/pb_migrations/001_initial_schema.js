/// <reference path="../pb_data/types.d.ts" />

migrate(
  (app) => {
    // ── Jobs collection ───────────────────────────────────────────
    const jobs = new Collection({
      name: "jobs",
      type: "base",
      fields: [
        { name: "slug", type: "text" },
        { name: "company", type: "text", required: true },
        { name: "role", type: "text", required: true },
        { name: "jd_url", type: "url" },
        { name: "jd_text", type: "text", maxSize: 0 },
        { name: "jd_cleaned", type: "text", maxSize: 0 },
        { name: "date_added", type: "date" },
        { name: "date_posted", type: "date" },
        { name: "pipeline_stage", type: "text" },
        { name: "score", type: "number" },
        { name: "hours", type: "number" },
        { name: "verdict", type: "text" },
      ],
      indexes: ['CREATE UNIQUE INDEX idx_jobs_slug ON jobs (slug)'],
      listRule: "",
      viewRule: "",
      createRule: "",
      updateRule: "",
      deleteRule: "",
    });
    app.save(jobs);

    // ── Sections collection ───────────────────────────────────────
    const sections = new Collection({
      name: "sections",
      type: "base",
      fields: [
        {
          name: "job",
          type: "relation",
          required: true,
          collectionId: jobs.id,
          cascadeDelete: true,
        },
        { name: "section_key", type: "text" },
        { name: "phase", type: "text" },
        { name: "status", type: "text" },
        { name: "content_md", type: "text", maxSize: 0 },
        { name: "model", type: "text" },
        { name: "tokens_used", type: "number" },
        { name: "generation_time_ms", type: "number" },
        { name: "error_message", type: "text", maxSize: 0 },
        { name: "is_locked", type: "bool" },
      ],
      indexes: [
        'CREATE UNIQUE INDEX idx_sections_job_key ON sections (job, section_key)',
      ],
      listRule: "",
      viewRule: "",
      createRule: "",
      updateRule: "",
      deleteRule: "",
    });
    app.save(sections);
  },
  (app) => {
    // Rollback
    const sections = app.findCollectionByNameOrId("sections");
    app.delete(sections);

    const jobs = app.findCollectionByNameOrId("jobs");
    app.delete(jobs);
  }
);
