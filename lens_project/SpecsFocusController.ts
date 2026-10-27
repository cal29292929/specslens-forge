// SpecsFocusController.ts — Lens Studio 5.15+ / Spectacles Interaction Kit (SIK)
// Target: Snap Spectacles ('24) | Comfort Zone: <= 25 deg HFOV, 0.65m..2.50m depth
@component
export class SpecsFocusController extends BaseScriptComponent {
  @input worldQueryModule: Asset;
  @input asrModule: Asset;
  @input maxConcurrentTimers: number = 6;

  onAwake(): void {
    print("SpecsFocusController initialized within 25-deg HFOV optical comfort envelope.");
  }
}
