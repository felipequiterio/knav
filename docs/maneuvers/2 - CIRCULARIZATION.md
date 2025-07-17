# Orbit Circularization

## 🚀 Introduction

Once a launch vehicle has reached a highly-elliptical *parking* orbit its next task is to **circularise**—i.e. adjust its periapsis and apoapsis so that both radii are equal and the eccentricity becomes (nearly) zero.  A circular orbit is desirable because

* the spacecraft’s **altitude and velocity remain constant**, simplifying subsequent manoeuvres,
* on-orbit operations (docking, rendezvous, station-keeping) are easier and safer, and
* mission planning tools usually assume circular reference orbits.

The manoeuvre typically consists of **two short ∆V burns** executed at opposite apsides of the ellipse:

1. **Raise periapsis** at the apoapsis burn.
2. **Lower apoapsis** at the periapsis burn (often negligible if the first burn is accurate).

---

## 🔬 Physics

### 1&nbsp;·&nbsp;Vis-viva equation

An object in a Keplerian orbit obeys

\[
  v(r) = \sqrt{\mu\left(\frac{2}{r} - \frac{1}{a}\right)}\,,
\]

where

* \(v(r)\) — orbital speed at radius \(r\),
* \(\mu = G\,M\) — gravitational parameter of the central body,
* \(a\) — semi-major axis of the orbit.

For a *circular* orbit \(r = a\) and the speed simplifies to

\[
  v_{\text{circ}} = \sqrt{\mu / r}\,.
\]

### 2&nbsp;·&nbsp;∆V at apoapsis

Starting from an ellipse with apoapsis radius \(r_a\) and periapsis radius \(r_p\) the semi-major axis is \(a = \tfrac12(r_a + r_p)\).  The speed **at apoapsis** is

\[
  v_a = v(r_a) = \sqrt{\mu\left(\frac{2}{r_a} - \frac{1}{a}\right)}\,,
\]

whereas the speed required for a circular orbit of radius \(r_a\) is

\[
  v_{\text{circ,a}} = \sqrt{\mu / r_a}\,.
\]

Hence the required prograde burn magnitude is

\[
  \Delta v_1 = v_{\text{circ,a}} - v_a\,.
\]

### 3&nbsp;·&nbsp;∆V at periapsis

After the first burn a new ellipse has periapsis \(r_p\) and apoapsis \(r_a' \approx r_a\).  Re-evaluating the same logic at **periapsis** yields a second burn

\[
  \Delta v_2 = v_{\text{circ,p}} - v_p\,.
\]

Often \(|\Delta v_2| < 1\;\text{m s}^{-1}\) and is skipped.

### 4&nbsp;·&nbsp;Burn-time estimation

`core/utils/formulas.py` implements the analytical burn-time estimate

\[
  t_{\text{burn}} = \frac{m_0 - m_1}{\dot m} \,,\quad m_1 = m_0\,e^{-\Delta v/(I_{sp}g_0)}\,,\quad \dot m = \frac{T}{I_{sp}g_0}\,.
\]

This expression derives from the **ideal rocket equation** and assumes constant thrust.

---

## 📝 Variables

| Symbol | Python stream / value | Description |
|--------|-----------------------|-------------|
| \(\mu\) | `body.gravitational_parameter` | Gravitational parameter [m³ s⁻²] |
| \(r_a\) | `vsl.orbit.apoapsis` | Current apoapsis radius [m] |
| \(r_p\) | `vsl.orbit.periapsis` | Current periapsis radius [m] |
| \(a\) | `0.5 * (r_a + r_p)` | Semi-major axis [m] |
| \(v_a\) | `vis_viva(mu, r_a, a)` | Speed at apoapsis [m s⁻¹] |
| \(v_p\) | `vis_viva(mu, r_p, a_new)` | Speed at periapsis after first burn |
| \(v_{\text{circ}}\) | `math.sqrt(mu / r)` | Circular-orbit speed [m s⁻¹] |
| \(\Delta v_{1,2}\) | computed deltas | Burn magnitudes [m s⁻¹] |
| \(I_{sp}\) | `vsl.specific_impulse` | Specific impulse [s] |
| \(g_0\) | `body.surface_gravity` | Reference gravity [m s⁻²] |
| \(\dot m\) | `vsl.available_thrust / (Isp * g0)` | Mass-flow rate [kg s⁻¹] |

These feed into `vis_viva()` and `calculate_burn_time()` in `core/utils/formulas.py`.

---

## ➗ Formulas & Code Mapping

```python
#   core/orbital/circularization.py (excerpt)

a = 0.5 * (r_a + r_p)

v_a      = vis_viva(mu, r_a, a)
v_circ   = math.sqrt(mu / r_a)
Δv1      = v_circ - v_a
node1    = vsl.control.add_node(ut_apo, prograde=Δv1)
...
# Burn-time estimate
m_dot    = vsl.available_thrust / (Isp * g0)
Δt_burn1 = calculate_burn_time(m_dot, m0, Δv1, Isp, g0)
```

The Python expressions mirror the analytical relations given above—`vis_viva()` is the direct implementation of the vis-viva equation, while `calculate_burn_time()` encapsulates the rocket-equation logic.

---

## 📜 Procedure Outline

1. **Measure** the current orbital parameters (`r_a`, `r_p`).
2. **Compute** \(\Delta v_1\) at apoapsis using vis-viva & circular speed.
3. **Create** a maneuver node at the apoapsis time and **warp** to \(T\!-
\Delta t/2\).
4. **Align** the vessel with the node (SAS “maneuver-hold”) and **execute** the burn, feathering throttle for precision.
5. **Audit** residual ∆V and **remove** the node.
6. **Re-evaluate** orbit; if \(|\Delta v_2| > 1\,\text{m s}^{-1}|\) repeat the process at periapsis.
7. **Log** final periapsis, apoapsis, eccentricity, and orbital period.

---

*Last updated: {{< DATE_PLACEHOLDER >}}*
