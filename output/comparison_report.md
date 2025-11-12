# AI生成ルール vs 手作りルール：詳細比較レポート

## 実行結果の比較

### AI生成ルール (generated_rule.yaml)

**コマンド:**
```bash
python rule_engine.py output/generated_rule.yaml test_data/source/sample1_small_factory.json output/ai_output_small_factory.json
```

**出力:**
```json
{
  "@context": {
    "target": "http://example.org/ghg-report#",
    "xsd": "http://www.w3.org/2001/XMLSchema#"
  },
  "@type": "target:Emission",
  "emission_source": "Unknown",
  "source_category": "Unknown",
  "energy_consumption_records": [{}, {}],
  "total_scope1": 0,
  "total_scope2": 0,
  "total_emissions": 0
}
```

**結果:** ❌ **失敗** - Total emissions: 0 kg-CO2

---

### 手作りルール (transformation_rules.yaml)

**コマンド:**
```bash
python rule_engine.py transformation_rules.yaml test_data/source/sample1_small_factory.json output/correct_output.json
```

**出力:**
```json
{
  "@context": {
    "ghg": "http://example.org/ghg-report#",
    "xsd": "http://www.w3.org/2001/XMLSchema#"
  },
  "@type": "ghg:EmissionReport",
  "reporting_organization": {
    "organization_name": "Acme Manufacturing Ltd",
    "@type": "ghg:Organization"
  },
  "emissions": [
    {
      "@type": "ghg:Scope2Emission",
      "emission_source": "Factory Tokyo Plant 1 - Widget Assembly Line A",
      "source_category": "electricity",
      "co2_amount": 6250.0,
      "calculation_method": "Activity-based calculation using standard emission factors",
      "emission_factor": 0.5,
      "activity_data": {
        "activity_id": "ACT-2024-001",
        "energy_amount": 12500,
        "energy_unit": "kWh",
        "start_date": "2024-01-01",
        "end_date": "2024-01-31"
      }
    },
    {
      "@type": "ghg:Scope1Emission",
      "emission_source": "Factory Tokyo Plant 1 - Widget Assembly Line A",
      "source_category": "natural_gas",
      "co2_amount": 1725.5,
      "calculation_method": "Activity-based calculation using standard emission factors",
      "emission_factor": 2.03,
      "activity_data": {
        "activity_id": "ACT-2024-001",
        "energy_amount": 850,
        "energy_unit": "m³",
        "start_date": "2024-01-01",
        "end_date": "2024-01-31"
      }
    },
    {
      "@type": "ghg:Scope2Emission",
      "emission_source": "Factory Tokyo Plant 1 - Component Machining",
      "source_category": "electricity",
      "co2_amount": 4200.0,
      "calculation_method": "Activity-based calculation using standard emission factors",
      "emission_factor": 0.5,
      "activity_data": {
        "activity_id": "ACT-2024-002",
        "energy_amount": 8400,
        "energy_unit": "kWh",
        "start_date": "2024-01-01",
        "end_date": "2024-01-31"
      }
    }
  ],
  "total_scope1": 1725.5,
  "total_scope2": 10450.0,
  "total_emissions": 12175.5,
  "reporting_period": "2024-01",
  "report_id": "GHG-AML-2024-01",
  "report_date": "2025-11-12"
}
```

**結果:** ✅ **成功** - Total emissions: 12,175.5 kg-CO2

---

## フィールド別比較

| フィールド | AI生成ルール | 手作りルール | 状態 |
|-----------|-------------|-------------|------|
| **@type** | `target:Emission` | `ghg:EmissionReport` | ✅ 両方正常 |
| **reporting_organization** | ❌ なし | ✅ "Acme Manufacturing Ltd" | ❌ AI失敗 |
| **emission_source** | ❌ "Unknown" | ✅ "Factory Tokyo Plant 1 - ..." | ❌ AI失敗 |
| **source_category** | ❌ "Unknown" | ✅ "electricity", "natural_gas" | ❌ AI失敗 |
| **emissions array** | ❌ 空の配列 `[{}, {}]` | ✅ 3件の詳細レコード | ❌ AI失敗 |
| **co2_amount** | ❌ なし | ✅ 6250.0, 1725.5, 4200.0 | ❌ AI失敗 |
| **emission_factor** | ❌ なし | ✅ 0.5, 2.03, 0.5 | ❌ AI失敗 |
| **activity_data** | ❌ なし | ✅ 詳細な活動データ | ❌ AI失敗 |
| **total_scope1** | ❌ 0 | ✅ 1725.5 | ❌ AI失敗 |
| **total_scope2** | ❌ 0 | ✅ 10450.0 | ❌ AI失敗 |
| **total_emissions** | ❌ 0 | ✅ 12175.5 | ❌ AI失敗 |
| **reporting_period** | ❌ なし | ✅ "2024-01" | ❌ AI失敗 |
| **report_id** | ❌ なし | ✅ "GHG-AML-2024-01" | ❌ AI失敗 |

## 排出量計算の検証

### 入力データ
```json
{
  "manufacturing_activities": [
    {
      "activity_id": "ACT-2024-001",
      "energy_consumptions": [
        {"energy_type": {"name": "electricity"}, "amount": 12500, "unit": "kWh"},
        {"energy_type": {"name": "natural_gas"}, "amount": 850, "unit": "m³"}
      ]
    },
    {
      "activity_id": "ACT-2024-002",
      "energy_consumptions": [
        {"energy_type": {"name": "electricity"}, "amount": 8400, "unit": "kWh"}
      ]
    }
  ]
}
```

### 手作りルールでの計算 (正しい)

**排出係数 (transformation_rules.yaml):**
```yaml
emission_factors:
  electricity: 0.500   # kg-CO2/kWh
  natural_gas: 2.03    # kg-CO2/m³
```

**計算:**
1. **ACT-2024-001 - 電力:**
   - 12,500 kWh × 0.5 kg-CO2/kWh = **6,250.0 kg-CO2** (Scope 2)

2. **ACT-2024-001 - 天然ガス:**
   - 850 m³ × 2.03 kg-CO2/m³ = **1,725.5 kg-CO2** (Scope 1)

3. **ACT-2024-002 - 電力:**
   - 8,400 kWh × 0.5 kg-CO2/kWh = **4,200.0 kg-CO2** (Scope 2)

**合計:**
- Scope 1: **1,725.5 kg-CO2**
- Scope 2: **10,450.0 kg-CO2** (6,250.0 + 4,200.0)
- **総排出量: 12,175.5 kg-CO2** ✅

---

### AI生成ルールでの計算 (失敗)

**排出係数 (generated_rule.yaml):**
```yaml
emission_factors:
  electricity: 0.4532  # kg-CO2/kWh (近い)
  natural_gas: 0.0543  # kg-CO2/m³ (間違い！実際の40分の1)
```

**問題:**
1. **substepsが空** → フィールドマッピングが実行されない
2. **計算ルールが参照されていない** → CO2計算が実行されない
3. **排出係数が不正確** → natural_gasが40倍過小評価

**実際の出力:**
- Scope 1: **0 kg-CO2** ❌
- Scope 2: **0 kg-CO2** ❌
- **総排出量: 0 kg-CO2** ❌

---

## ルール構造の比較

### Transformation Steps

#### AI生成ルール ❌
```yaml
transformation_steps:
- name: extract_energy_consumptions
  source: manufacturing_activities
  target: energy_consumption_records
  iteration: true
  substeps: []  # ← 空！何もマッピングされない
```

**問題:**
- Substepsが空
- 何をどうマッピングするのか指定されていない
- 結果: 空のオブジェクト `[{}, {}]` が生成される

#### 手作りルール ✅
```yaml
transformation_steps:
  - name: "transform_activities_to_emissions"
    source: "manufacturing_activities"
    target: "emissions"
    iteration: true
    substeps:
      - name: "transform_energy_to_emission"
        source: "$.energy_consumptions"
        iteration: true
        mapping:
          # 排出タイプの決定
          - target: "@type"
            calculation: "determine_scope"
            format: "ghg:Scope{scope}Emission"

          # 排出源の生成
          - target: "emission_source"
            calculation: "generate_emission_source"
            context: "parent"

          # エネルギータイプ
          - target: "source_category"
            source: "$.energy_type.name"
            transform: "lowercase_underscore"

          # CO2排出量の計算
          - target: "co2_amount"
            calculation: "calculate_co2_emission"
            rounding: 2

          # 計算方法
          - target: "calculation_method"
            fixed_value: "${constants.defaults.calculation_method}"

          # 排出係数
          - target: "emission_factor"
            calculation: "calculate_co2_emission"
            extract_field: "emission_factor"

          # 活動データのネスト
          - target: "activity_data.activity_id"
            source: "activity_id"
            context: "parent"
          - target: "activity_data.energy_amount"
            source: "$.amount"
          - target: "activity_data.energy_unit"
            source: "$.unit"
```

**特徴:**
- 詳細なsubsteps
- 各フィールドのマッピングを明示
- 計算ルールの参照
- コンテキストの使用（parent）

---

### Calculation Rules

#### AI生成ルール ❌
```yaml
calculation_rules:
- name: co2_emission_calculation
  formula: energy_consumption.amount * emission_factor_lookup[energy_type.energy_type_name]
```

**問題:**
1. Transformation stepsで参照されていない
2. `formula`の構文がrule_engineで実行できない
3. `input`フィールドがない

#### 手作りルール ✅
```yaml
calculation_rules:
  - name: "calculate_co2_emission"
    description: "Convert energy consumption to CO2 emissions"
    input:
      energy_amount: "$.amount"
      energy_type: "$.energy_type.name"
    formula: "energy_amount * emission_factor"
    lookup:
      emission_factor:
        source: "constants.emission_factors"
        key: "energy_type"
        key_transform: "lowercase_underscore"
        default: "${constants.defaults.default_emission_factor}"
    output: "co2_amount"
    rounding: 2
```

**特徴:**
- 明確な`input`定義
- `lookup`でemission_factorsから値を取得
- `key_transform`で名前を正規化
- `rounding`で小数点以下を制御

---

## なぜAI生成ルールは失敗したのか？

### 根本原因の詳細分析

#### 1. **Substepsの欠如** (最重要)
```yaml
# AI生成 ❌
substeps: []

# 正しい例 ✅
substeps:
  - name: "transform_energy_to_emission"
    source: "$.energy_consumptions"
    iteration: true
    mapping: [...]
```

**影響:**
- フィールドがマッピングされない
- 空のオブジェクトが生成される
- すべての計算がスキップされる

#### 2. **データ構造の理解不足**
AIは以下を理解できていません：
- `manufacturing_activities`が配列
- 各activityに`energy_consumptions`配列がネストされている
- 2段階の反復処理が必要（activities → energy_consumptions）

#### 3. **Rule Engineの構文理解不足**
```yaml
# AI生成（動作しない）❌
formula: energy_consumption.amount * emission_factor_lookup[energy_type.energy_type_name]

# 正しい構文 ✅
formula: "energy_amount * emission_factor"
lookup:
  emission_factor:
    source: "constants.emission_factors"
    key: "energy_type"
```

#### 4. **計算ルールの未接続**
AI生成の計算ルールは定義されているが、transformation_stepsで参照されていない：

```yaml
# AI生成のtransformation_steps ❌
mapping: []  # 計算ルールへの参照なし

# 正しい例 ✅
mapping:
  - target: "co2_amount"
    calculation: "calculate_co2_emission"  # 計算ルールを参照
```

---

## AI Generatorの改善が必要な点

### 1. **Substeps生成の強制** 🔴 重要度: 最高

現在:
```yaml
substeps: []
```

必要:
```yaml
substeps:
  - name: "具体的な変換名"
    source: "$.nested_field"
    iteration: true
    mapping: [...]
```

### 2. **サンプルデータ入力の追加** 🔴 重要度: 高

```python
# 現在
generator = AIRuleGenerator(source_ontology, target_ontology)

# 提案
generator = AIRuleGenerator(
    source_ontology,
    target_ontology,
    sample_source_data="sample_input.json"  # 追加
)
```

**効果:**
- AIが実際のJSONデータ構造を理解
- ネストした配列を正しく処理
- フィールド名を正確にマッピング

### 3. **Rule Engine構文のガイド強化** 🟡 重要度: 中

AIプロンプトに以下を追加:
```
Calculation rules must use this format:
- input: Define input fields with JSONPath
- formula: Simple arithmetic expression using input field names
- lookup: For constant lookups (not inline dictionary access)
- output: Target field name
```

### 4. **生成後の検証** 🟡 重要度: 中

```python
# 生成されたルールをサンプルデータで検証
validator = RuleValidator(generated_rules, sample_data)
errors = validator.validate()
if errors:
    # AIに修正を依頼
    fixed_rules = generator.fix_rules(errors)
```

---

## 推奨事項

### 短期的な解決策（今すぐ）

1. **手作りルールを使用** ✅
   ```bash
   python rule_engine.py transformation_rules.yaml input.json output.json
   ```

2. **AI生成ルールを手動で修正**
   - Substepsを追加
   - Field mappingsを具体化
   - Calculation rulesを接続

### 中期的な改善（次のバージョン）

1. **AI Generator v2の開発**
   - サンプルデータ入力機能
   - Substeps生成の強制
   - 自動検証機能

2. **ハイブリッドアプローチ**
   - AIが初期ドラフトを生成
   - ユーザーがGUIで確認・修正
   - 修正内容をAIにフィードバック

### 長期的なビジョン

1. **学習機能の追加**
   - 手動修正をAIが学習
   - 類似パターンを自動認識

2. **対話的なルール生成**
   ```
   AI: "manufacturing_activitiesをどのフィールドに変換しますか？"
   User: "emissionsに変換"
   AI: "energy_consumptionsの処理方法は？"
   User: "各消費レコードをemissionレコードに変換"
   ```

---

## まとめ

### AI生成ルールの評価

| 評価項目 | スコア | コメント |
|---------|-------|---------|
| **概念理解** | ⭐⭐⭐⭐☆ | クラスマッピング、計算、集約を正しく識別 |
| **構文正確性** | ⭐☆☆☆☆ | Rule Engine構文を理解していない |
| **実装完全性** | ⭐☆☆☆☆ | Substepsが空、使用不可 |
| **排出係数** | ⭐⭐☆☆☆ | 値が不正確（特にnatural_gas） |
| **データ構造理解** | ⭐☆☆☆☆ | ネストした配列を処理できない |
| **総合評価** | ⭐⭐☆☆☆ | 概念的には正しいが実装が不完全 |

### 結論

**AI生成ルール:**
- ✅ 高レベルの変換ロジックは理解している
- ❌ 実装の詳細が欠けている
- ❌ そのままでは使用不可
- ⚠️ 手動修正が必須

**手作りルール:**
- ✅ すべてのフィールドが正しくマッピング
- ✅ 計算が正確に実行
- ✅ 総排出量: 12,175.5 kg-CO2
- ✅ すぐに使用可能

**推奨:**
当面は手作りの`transformation_rules.yaml`を使用し、AI Generatorの改善を進める。
