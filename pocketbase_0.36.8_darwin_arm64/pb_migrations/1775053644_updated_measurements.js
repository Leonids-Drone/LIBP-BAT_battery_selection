/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const collection = app.findCollectionByNameOrId("pbc_638208807")

  // add field
  collection.fields.addAt(2, new Field({
    "hidden": false,
    "id": "number2853863016",
    "max": null,
    "min": null,
    "name": "sn_num",
    "onlyInt": false,
    "presentable": false,
    "required": false,
    "system": false,
    "type": "number"
  }))

  return app.save(collection)
}, (app) => {
  const collection = app.findCollectionByNameOrId("pbc_638208807")

  // remove field
  collection.fields.removeById("number2853863016")

  return app.save(collection)
})
