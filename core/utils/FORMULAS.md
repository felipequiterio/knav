# Physics & Orbital Mechanics Formulas

This document explains every helper function found in `core/utils/formulas.py`. For each formula you will find:

• **What it calculates / why it matters**  
• **Where it is used in the code-base** (so you can trace practical examples)  
• **Mathematical expression (LaTeX)**  
• **Python implementation** – the relevant one-liner or short block from the source file

---

## 1. `gravity_local(μ, r)`

**Description**: Local gravitational acceleration at an arbitrary radius *r* from the centre of a body with gravitational parameter *μ*.

**Used in**:

- `core/launch/gravity_turn.py` – pre-launch checks (`grav_local` lambda)

**Formula (LaTeX)**:
\[
    g = \frac{\mu}{r^{2}}
\]

**Code**

```python
# core/utils/formulas.py
g = μ / r**2
```

---

## 2. `thrust_to_weight(F_thrust, m, g)`

**Description**: Dimensionless thrust-to-weight ratio (TWR) of a vessel; a critical indicator of whether a craft can lift off a planetary surface.

**Used in**:

- `core/launch/gravity_turn.py` – launch-readiness check (`thrust_to_weight_ratio` lambda)

**Formula (LaTeX)**:
\[
    \text{TWR} = \frac{F_{\text{thrust}}}{m\, g}
\]

**Code**

```python
twr = F_thrust / (m * g)
```

---

## 3. `acceleration(F_thrust, m)`

**Description**: Instantaneous linear acceleration produced by the vessel’s engines when throttle is fully open.*¹*

**Used in**:

- `core/launch/gravity_turn.py` – sanity check before committing to ascent (`accel` lambda)

**Formula (LaTeX)**:
\[
    a = \frac{F_{\text{thrust}}}{m}
\]

**Code**

```python
a = F_thrust / m
```

*¹* kRPC does not expose live acceleration directly, so we compute it from thrust and mass.

---

## 4. `surface_gravity(μ, r)`

**Description**: Gravitational acceleration **at the surface** of a celestial body (simply `gravity_local` evaluated at the equatorial radius).

**Used in**:

- (Currently not referenced – kept for convenience / possible future telemetry.)

**Formula (LaTeX)**:
\[
    g_{0} = \frac{\mu}{r^{2}}
\]

**Code**

```python
g0 = μ / r**2
```

---

## 5. `vis_viva(μ, r, a)`

**Description**: Instantaneous orbital velocity given radius *r* and semi-major axis *a* (the vis-viva equation).

**Used in**:

- `core/orbital/circularization.py` – to compute current velocity at apoapsis / periapsis for burns

**Formula (LaTeX)**:
\[
    v = \sqrt{\mu \left( \frac{2}{r} - \frac{1}{a} \right)}
\]

**Code**

```python
v = math.sqrt(μ * (2 / r - 1 / a))
```

---

## 6. `delta_v_hohmann(μ, r1, r2)`

**Description**: ∆v requirements for the two burns of a classical Hohmann transfer between two coplanar circular orbits of radii *r₁* → *r₂*.

**Used in**:

- `core/orbital/hohmann_transfer.py` – planning outbound inter-moon / inter-planet transfers

**Formulae (LaTeX)**:
\[
    \begin{aligned}
    \Delta v_{1} &= \sqrt{\frac{\mu}{r_{1}}}\,\Bigl(\sqrt{\frac{2 r_{2}}{r_{1}+r_{2}}}-1\Bigr) \\
    \Delta v_{2} &= \sqrt{\frac{\mu}{r_{2}}}\,\Bigl(1-\sqrt{\frac{2 r_{1}}{r_{1}+r_{2}}}\Bigr)
    \end{aligned}
\]

**Code**

```python
dv1 = math.sqrt(mu / r1) * (math.sqrt(2 * r2 / (r1 + r2)) - 1)
dv2 = math.sqrt(mu / r2) * (1 - math.sqrt(2 * r1 / (r1 + r2)))
```

---

## 7. `calculate_burn_time(g0, F, Isp, m0, ∆v)`

**Description**: Estimates how long an engine burn must last to achieve a desired ∆v, given the current thrust, specific impulse, local standard gravity, and starting mass.

**Used in**:

- `core/orbital/circularization.py` – timing periapsis/apoapsis burns
- `core/orbital/hohmann_transfer.py` – centring maneuver nodes on burn mid-point

**Parameters**:  
• *g₀* — reference gravity at the body's surface (m s⁻²)  
• *F* — available thrust (N)  
• *Isp* — specific impulse (s)  
• *m₀* — initial mass (kg)  
• *∆v* — required velocity change (m/s)

**Underlying maths (LaTeX)**:
\[
    m_{1}= \frac{m_{0}}{e^{\Delta v/(I_{sp} g_{0})}}, \quad
    \dot m = \frac{F}{I_{sp} g_{0}}, \quad
    t = \frac{m_{0}-m_{1}}{\dot m}
\]

**Code (key lines)**

```python
m1 = m0 / math.exp(delta_v / (Isp * g0))
flow_rate = F / (Isp * g0)
burn_time = (m0 - m1) / flow_rate
```

---

## 8. `calculate_transfer_time(μ, r1, r2)`

**Description**: Time required to traverse the **transfer ellipse** of a Hohmann transfer (half an elliptic orbit).

**Used in**:

- `core/orbital/hohmann_transfer.py` – phase-angle & window calculation

**Formula (LaTeX)**:
\[
    t = \pi \sqrt{\frac{(r_{1}+r_{2})^{3}}{8\mu}}
\]

**Code**

```python
t = math.pi * math.sqrt((r2 + r1) ** 3 / (8 * mu))
```

---

## 9. `calculate_target_period(μ, r)`

**Description**: Orbital period of a circular orbit with radius *r* around a body of parameter *μ*. Although not yet called directly, the same expression is replicated inside `hohmann_transfer.py`.

**Used in**:

- (Not directly invoked – potential future replacement for inline calculation.)

**Formula (LaTeX)**:
\[
    T = 2\pi \sqrt{\frac{r^{3}}{\mu}}
\]

**Code**

```python
T = 2 * math.pi * math.sqrt(r**3 / mu)
```

---

### Cross-reference summary

| Function | Primary module(s) that call it |
|----------|--------------------------------|
| `gravity_local` | `gravity_turn.py` |
| `thrust_to_weight` | `gravity_turn.py` |
| `acceleration` | `gravity_turn.py` |
| `surface_gravity` | – |
| `vis_viva` | `circularization.py` |
| `delta_v_hohmann` | `hohmann_transfer.py` |
| `calculate_burn_time` | `circularization.py`, `hohmann_transfer.py` |
| `calculate_transfer_time` | `hohmann_transfer.py` |
| `calculate_target_period` | – |
