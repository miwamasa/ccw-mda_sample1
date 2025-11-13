# AI生成ルールの分析結果

## 実行結果

### コマンド
```bash
python rule_engine.py output/generated_rule.yaml test_data/source/sample1_small_factory.json output/ai_output_small_factory.json
```

### 出力
```json
{
  "@context": {
    "target": "http://example.org/ghg-report#",
    "xsd": "http://www.w3.org/2001/XMLSchema#"
  },
  "@type": "target:Emission",
  "emission_source": "Unknown",
  "source_category": "Unknown",
  "energy_consumption_records": [
    {},
    {}
  ],
  "total_scope1": 0,
  "total_scope2": 0,
  "total_emissions": 0
}
```

### 結果
❌ **失敗** - すべてのフィールドが空またはデフォルト値

## 問題分析

### 問題1: フィールドマッピングが不完全 ❌

**AI生成ルール:**
```yaml
field_mappings:
- source_path: activity_name
  target_path: emission_source
  default: ${constants.defaults.unknown_value}
```

**問題:**
- `activity_name`は配列`manufacturing_activities[]`の中にある
- ルートレベルには存在しない
- 結果: `"emission_source": "Unknown"` (デフォルト値)

**正しい例 (transformation_rules.yaml):**
```yaml
field_mappings:
  - source_path: "organization.name"
    target_path: "reporting_organization.organization_name"
```

### 問題2: Transformation Stepsのsubstepsが空 ❌

**AI生成ルール:**
```yaml
transformation_steps:
- name: extract_energy_consumptions
  source: manufacturing_activities
  target: energy_consumption_records
  iteration: true
  substeps: []  # ← 空！
```

**問題:**
- `substeps`が空なので、何もマッピングされない
- `source`から`target`へのコピーだけが行われる
- フィールドの中身が空のまま

**結果:**
```json
"energy_consumption_records": [
  {},  // 空のオブジェクト
  {}   // 空のオブジェクト
]
```

**正しい例 (transformation_rules.yaml):**
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
          - target: "@type"
            calculation: "determine_scope"
            format: "ghg:Scope{scope}Emission"
          - target: "emission_source"
            calculation: "generate_emission_source"
            context: "parent"
          - target: "energy_type"
            source: "$.energy_type.name"
            transform: "lowercase_underscore"
          - target: "co2_amount"
            calculation: "calculate_co2_emission"
            rounding: 2
```

### 問題3: 計算ルールが実行されない ❌

**AI生成ルール:**
```yaml
calculation_rules:
- name: co2_emission_calculation
  formula: energy_consumption.amount * emission_factor_lookup[energy_type.energy_type_name]
```

**問題:**
- transformation_stepsでこの計算ルールが参照されていない
- `formula`の構文がrule_engineでサポートされていない（Pythonコードとして実行できない）
- 計算が一度も実行されない

**正しい例:**
```yaml
calculation_rules:
  - name: "calculate_co2_emission"
    input:
      energy_amount: "$.amount"
      energy_type: "$.energy_type.name"
    formula: "energy_amount * emission_factor"
    lookup:
      emission_factor:
        source: "constants.emission_factors"
        key: "energy_type"
```

### 問題4: 排出係数の値が不正確 ⚠️

**AI生成ルール:**
```yaml
constants:
  emission_factors:
    electricity: 0.4532     # kg-CO2/kWh
    natural_gas: 0.0543     # ← これは間違い！
```

**実際の標準値:**
```yaml
constants:
  emission_factors:
    electricity: 0.500      # kg-CO2/kWh
    natural_gas: 2.03       # kg-CO2/m³ (正しい値)
    diesel: 2.68            # kg-CO2/liter
```

**影響:**
- natural_gasの係数が約40分の1しかない
- 計算結果が大幅に過小評価される

## 期待される正しい出力

**正しいルール (transformation_rules.yaml) を使用した場合:**

```json
{
  "@context": {
    "ghg": "http://example.org/ghg-report#",
    "xsd": "http://www.w3.org/2001/XMLSchema#"
  },
  "@type": "ghg:EmissionReport",
  "report_id": "GHG-AML-2024-01",
  "reporting_organization": {
    "@type": "ghg:Organization",
    "organization_name": "Acme Manufacturing Ltd"
  },
  "reporting_period": "2024-01",
  "calculation_method": "Activity-based calculation using standard emission factors",
  "emissions": [
    {
      "@type": "ghg:Scope2Emission",
      "emission_source": "Factory Tokyo Plant 1 - Widget Assembly Line A",
      "activity_reference": "ACT-2024-001",
      "energy_type": "electricity",
      "energy_amount": 12500,
      "energy_unit": "kWh",
      "emission_factor": 0.5,
      "co2_amount": 6250.0,
      "scope": 2
    },
    {
      "@type": "ghg:Scope1Emission",
      "emission_source": "Factory Tokyo Plant 1 - Widget Assembly Line A",
      "activity_reference": "ACT-2024-001",
      "energy_type": "natural_gas",
      "energy_amount": 850,
      "energy_unit": "m³",
      "emission_factor": 2.03,
      "co2_amount": 1725.5,
      "scope": 1
    },
    {
      "@type": "ghg:Scope2Emission",
      "emission_source": "Factory Tokyo Plant 1 - Component Machining",
      "activity_reference": "ACT-2024-002",
      "energy_type": "electricity",
      "energy_amount": 8400,
      "energy_unit": "kWh",
      "emission_factor": 0.5,
      "co2_amount": 4200.0,
      "scope": 2
    }
  ],
  "total_scope1": 1725.5,
  "total_scope2": 10450.0,
  "total_emissions": 12175.5
}
```

## なぜAI生成ルールが失敗したのか？

### 根本原因

1. **抽象的すぎる変換ステップ**
   - AIは「extract_energy_consumptions」「calculate_emissions」という高レベルの概念的ステップを生成
   - しかし、具体的なフィールドマッピングを生成していない

2. **オントロジーとデータ構造のギャップ**
   - AIはオントロジーの構造を理解
   - しかし、実際のJSON-LDデータの**ネストした配列構造**を理解していない

3. **Rule Engineの機能理解不足**
   - AI生成の`formula`フィールドはrule_engineでサポートされていない構文
   - Substepsの構造が不完全

### AI Generatorの限界

現在のAI rule generatorは：
- ✅ オントロジーのクラス/プロパティの意味を理解
- ✅ 必要な計算や集約を概念的に理解
- ❌ 実際のJSON-LDデータ構造を知らない
- ❌ Rule Engineの具体的な構文を完全に理解していない
- ❌ Substepsの詳細なマッピングを生成できない

## 解決策

### オプション1: 手動でルールを修正 ✏️

AI生成ルールを基に、手動で`substeps`を追加：

```yaml
transformation_steps:
- name: extract_energy_consumptions
  source: manufacturing_activities
  target: emissions
  iteration: true
  substeps:
    - name: process_energy_consumption
      source: "$.energy_consumptions"
      iteration: true
      mapping:
        - target: "energy_type"
          source: "$.energy_type.name"
        - target: "amount"
          source: "$.amount"
        - target: "co2_amount"
          calculation: "co2_emission_calculation"
```

### オプション2: 正しいルールを使用 ✅ (推奨)

手作りの`transformation_rules.yaml`を使用：

```bash
python rule_engine.py \
    transformation_rules.yaml \
    test_data/source/sample1_small_factory.json \
    output/correct_output.json
```

### オプション3: サンプルデータを提供してAIを再教育 🔄

AI rule generatorを改善：
1. サンプルJSONデータも入力として受け取る
2. 実際のデータ構造を分析
3. より具体的なマッピングを生成

## 結論

**AI生成ルールの評価:**
- ✅ 概念的に正しい（適切な計算、集約、分類を認識）
- ✅ 排出係数を提案（値は不正確だが）
- ❌ 実装が不完全（substepsが空）
- ❌ 実際のデータ構造を反映していない
- ❌ そのままでは使用不可

**推奨アクション:**
1. **当面**: 手作りの`transformation_rules.yaml`を使用
2. **将来**: AI rule generatorの改善（サンプルデータ入力を追加）
3. **代替**: AI生成ルールをテンプレートとして、手動で完成させる

## 比較: AI生成 vs 手作り

| 項目 | AI生成 | 手作り (transformation_rules.yaml) |
|------|--------|-----------------------------------|
| 生成時間 | 5秒 | 数時間 |
| 正確性 | ❌ 低い | ✅ 高い |
| 完全性 | ❌ 不完全 | ✅ 完全 |
| 使用可能性 | ❌ 要修正 | ✅ すぐ使える |
| 排出係数 | ⚠️ 不正確 | ✅ 正確 |
| Substeps | ❌ 空 | ✅ 詳細 |

## 次のステップ

### すぐに使える解決策

```bash
# 正しいルールで変換を実行
python rule_engine.py \
    transformation_rules.yaml \
    test_data/source/sample1_small_factory.json \
    output/correct_output.json

# 結果を確認
cat output/correct_output.json | jq '.'
```

### AI Generatorの改善提案

1. **サンプルデータ入力の追加**
   ```python
   generator = AIRuleGenerator(
       source_ontology="source.ttl",
       target_ontology="target.ttl",
       sample_data="sample.json"  # 追加
   )
   ```

2. **より具体的なプロンプト**
   - Substepsの生成を強制
   - Rule Engineの構文を明示
   - 実際のデータ構造例を提供

3. **検証ステップの追加**
   - 生成されたルールをサンプルデータで検証
   - エラーがあればAIに修正を依頼
