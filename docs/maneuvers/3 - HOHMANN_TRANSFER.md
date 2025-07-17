# Hohmann Transfer

## 🚀 Introduction

A **Hohmann transfer** is the most fuel-efficient two-impulse manoeuvre for moving a spacecraft between **coplanar** circular orbits.  The craft first performs a prograde burn to enter an elliptical *transfer* orbit whose apoapsis (or periapsis) matches the target radius.  Half an orbital period later, a second burn circularises the orbit at the destination.

Why it matters:

* Minimises **∆V** — ideal in the absence of significant perturbations.
* Requires only **two short burns** separated by coasting time; guidance is simple.
* Forms the backbone of inter-planetary mission planning and rendezvous techniques.

---

## 🔬 Physics

Consider an initial circular orbit of radius \(r_1\) and a target circular orbit of radius \(r_2\) around the same central body with gravitational parameter \(\mu\).  The transfer ellipse has periapsis \(r_1\) and apoapsis \(r_2\).

### 1 · ∆V requirements

Using vis-viva, the orbital speeds just before each burn are

\[
  v_1 = \sqrt{\mu / r_1},\qquad
  v_2 = \sqrt{\mu / r_2},\qquad
  a   = \tfrac12\,(r_1 + r_2).
\]

Speeds **on the ellipse** at periapsis and apoapsis are

\[
  v_{p} = \sqrt{\mu\!\left(\frac{2}{r_1} - \frac{1}{a}\right)},\qquad
  v_{a} = \sqrt{\mu\!\left(\frac{2}{r_2} - \frac{1}{a}\right)}.
\]

Therefore the ideal impulses are

\[
\begin{aligned}
  \Delta v_1 &= v_{p} - v_1
             = \sqrt{\mu / r_1}\,\Bigl(\sqrt{\tfrac{2 r_2}{r_1 + r_2}} - 1\Bigr),\\[6pt]
  \Delta v_2 &= v_2 - v_{a}
             = \sqrt{\mu / r_2}\,\Bigl(1 - \sqrt{\tfrac{2 r_1}{r_1 + r_2}}\Bigr).
\end{aligned}
\]

These are implemented by `delta_v_hohmann()` in `core/utils/formulas.py`.

### 2 · Transfer time

The time of flight along half the transfer ellipse is

\[
  t_{\text{tr}} = \pi \sqrt{\frac{(r_1 + r_2)^3}{8\,\mu}}\,.
\]

`calculate_transfer_time()` provides this value for scheduling the departure window.

### 3 · Phase angle

For transfers to a **secondary body** (e.g. planetary moon), the burn must be timed such that the target arrives at the rendezvous point simultaneously.  The required phase angle (for outer targets) is approximately

\[
  \phi = 180^{\circ} - 360^{\circ}\,\frac{t_{\text{tr}}}{T_{\text{tgt}}},
\]

where \(T_{\text{tgt}}\) is the target’s orbital period around the common centre.  The code in `core/orbital/hohmann_transfer.py` computes this more precisely using mean anomalies.

---

## 📝 Variables

| Symbol | Python expression / stream | Meaning |
|--------|----------------------------|---------|
| \(\mu\) | `origin_body.gravitational_parameter` | Central-body GM [m³ s⁻²] |
| \(r_1\) | `vsl.orbit.semi_major_axis` | Initial orbit radius [m] |
| \(r_2\) | `target_body.orbit.semi_major_axis` | Target orbit radius [m] |
| \(\Delta v_{1,2}\) | `delta_v_hohmann(mu,r1,r2)` | Burn magnitudes [m s⁻¹] |
| \(t_{\text{tr}}\) | `calculate_transfer_time(mu,r1,r2)` | Transfer time [s] |
| \(\phi\) | computed via phase-angle maths | Required phase angle [deg] |
| \(I_{sp}\) | `vsl.specific_impulse` | Specific impulse [s] |
| \(g_0\) | `origin_body.surface_gravity` | Reference gravity [m s⁻²] |
| \(\dot m\) | `vsl.available_thrust/(Isp*g0)` | Mass-flow rate [kg s⁻¹] |

These variables feed into both the analytical formulas and the helper functions in `formulas.py`.

---

## ➗ Formulas & Code Mapping

```python
# core/orbital/hohmann_transfer.py (excerpt)

r1 = vsl.orbit.semi_major_axis
r2 = target_body.orbit.semi_major_axis

Δv1, Δv2 = delta_v_hohmann(mu, r1, r2)
transfer_time = calculate_transfer_time(mu, r1, r2)
phase_angle = 180 - (transfer_time / target_period) * 360
```

The Python calls invoke the exact equations derived above.  Burn-time estimation further relies on `calculate_burn_time()` which applies the ideal rocket equation.

---

## 📜 Procedure Outline

1. **Gather** current orbit radius \(r_1\) and target orbit radius \(r_2\).
2. **Compute** \(\Delta v_1\) and \(\Delta v_2\) using `delta_v_hohmann()`.
3. **Determine** transfer time \(t_{\text{tr}}\) and phase angle \(\phi\) to schedule departure.
4. **Warp** to \(T\! -\)lead-time seconds and create the manoeuvre node with prograde \(\Delta v_1\).
5. **Align** the vessel and execute the first burn, centring it on the node.
6. **Coast** for half an orbital period.
7. **Perform** the second burn of magnitude \(\Delta v_2\) to circularise at \(r_2\).
8. **Verify** final orbit parameters and log ∆V usage.

---

*Last updated: {{< DATE_PLACEHOLDER >}}*
