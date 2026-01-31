/// <reference path="../pb_data/types.d.ts" />

migrate((app) => {
  // Add created/updated autodate fields to jobs collection
  const jobs = app.findCollectionByNameOrId("jobs")
  jobs.fields.add(new Field({
    "hidden": false,
    "id": "autodate_created",
    "name": "created",
    "onCreate": true,
    "onUpdate": false,
    "system": false,
    "type": "autodate"
  }))
  jobs.fields.add(new Field({
    "hidden": false,
    "id": "autodate_updated",
    "name": "updated",
    "onCreate": true,
    "onUpdate": true,
    "system": false,
    "type": "autodate"
  }))
  app.save(jobs)

  // Add created/updated autodate fields to sections collection
  const sections = app.findCollectionByNameOrId("sections")
  sections.fields.add(new Field({
    "hidden": false,
    "id": "autodate_created",
    "name": "created",
    "onCreate": true,
    "onUpdate": false,
    "system": false,
    "type": "autodate"
  }))
  sections.fields.add(new Field({
    "hidden": false,
    "id": "autodate_updated",
    "name": "updated",
    "onCreate": true,
    "onUpdate": true,
    "system": false,
    "type": "autodate"
  }))
  app.save(sections)
}, (app) => {
  // Rollback - remove autodate fields
  const jobs = app.findCollectionByNameOrId("jobs")
  jobs.fields.removeById("autodate_created")
  jobs.fields.removeById("autodate_updated")
  app.save(jobs)

  const sections = app.findCollectionByNameOrId("sections")
  sections.fields.removeById("autodate_created")
  sections.fields.removeById("autodate_updated")
  app.save(sections)
})
