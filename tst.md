⚠️ Important scientific point

There may be multiple angles producing similar drag.

For example:

AoA = -3° → Cd = 0.025
AoA = +4° → Cd = 0.025

So our final optimizer should not simply pick the first one.

We should add a constraint such as:

Option A — Maximum lift

Find the target drag angle that gives maximum Cl.

Option B — Closest to current angle

Adjust the airfoil as little as possible.

Option C — User chooses the objective

For your project, I recommend Option A: target drag + maximum lift.

That makes the project much more interesting:

The system adjusts the angle of attack to achieve the required drag while maximizing lift.

After this optimizer works, the next step should be an automatic animated AoA adjustment, where the airfoil physically rotates from its current angle to the recommended angle.

Next we implement **target-drag control**.

Given:

```text
Airfoil geometry
Re
Ncrit
Target Cd
```

we search for the `alpha` that gives the closest predicted `Cd`.

### Step 1 — Target-Cd optimizer

```python
def optimize_alpha_for_target_cd(
    airfoil_features,
    re_value,
    ncrit_value,
    target_cd,
    alpha_min=-10,
    alpha_max=15
):
    def objective(alpha):
        _, cd = predict_aero(
            alpha,
            airfoil_features,
            re_value,
            ncrit_value
        )
        return abs(cd - target_cd)

    result = minimize_scalar(
        objective,
        bounds=(alpha_min, alpha_max),
        method="bounded"
    )

    best_alpha = result.x

    cl, cd = predict_aero(
        best_alpha,
        airfoil_features,
        re_value,
        ncrit_value
    )

    return {
        "target_Cd": target_cd,
        "optimal_alpha": best_alpha,
        "predicted_Cl": cl,
        "predicted_Cd": cd,
        "error": abs(cd - target_cd)
    }
```

### Step 2 — Test it

```python
target_result = optimize_alpha_for_target_cd(
    airfoil_features,
    re_value=500000,
    ncrit_value=9,
    target_cd=0.010
)

target_result
```

This is the first version of the behavior we originally wanted:

$$
\boxed{\alpha^*=\arg\min_\alpha |Cd_{pred}(\alpha)-Cd_{target}|}
$$

Run it and send me the result.




# Final Cl model
final_cl_model = xgb.XGBRegressor(
    n_estimators=400,
    learning_rate=0.08,
    max_depth=8,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="reg:squarederror",
    n_jobs=-1,
    random_state=42
)

final_cl_model.fit(X_train, y_train["Cl"])



# Final Cd model
final_cd_model = lgb.LGBMRegressor(
    n_estimators=400,
    learning_rate=0.08,
    num_leaves=50,
    max_depth=-1,
    min_child_samples=20,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_alpha=0.1,
    reg_lambda=0.1,
    random_state=42,
    n_jobs=-1,
    verbosity=-1
)

final_cd_model.fit(X_train, y_train["Cd"])