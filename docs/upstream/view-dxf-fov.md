<!-- Draft issue for tangency-labs/solidcraft. Title: -->
<!-- Export View as DXF: a camera without `fov` is refused as "invalid camera" -->

**Reproduced on:** SolidCraft 0.30.1 (release `solidcraft-cli-0.30.1-macos-universal`), macOS

### Steps
Minimal script (`solidcraft-cli run repro.json`):

```json
{"commands":[
 {"command":"solid.box","params":{"length":20,"width":10,"height":5}},
 {"command":"file.export_view_dxf","params":{"camera":{"target":[0,0,0],"yaw":0,"pitch":0,"distance":100}}}
]}
```

### Expected
The view is exported as an orthographic projection. Elsewhere `fov` is optional and defaults to orthographic: `docs/mcp.md` gives the camera as `{target, yaw, pitch, distance, fov?}`, and `solidcraft-cli snapshot --camera` and `view.apply` take the same object.

### Actual
```text
error: step 2 (file.export_view_dxf): invalid parameters for `file.export_view_dxf`: invalid camera
```
It fails every time (2 of 2 runs). With `"fov": 0` added, the same script succeeds.

The message doesn't say which field is wrong, so a camera copied from a `screenshot` call or the docs looks broken.
In `crates/engine/src/cmd/view_dxf.rs` the camera is deserialised straight into `solidcraft_render::Camera`, whose `fov` field has no `#[serde(default)]` (unlike `roll` and `up`).

### Attachments
None needed: the script above reproduces it in a fresh design.
