# AI生成ルールの問題と修正方法

## 問題の原因

AI rule generatorは**RDFオントロジーの構造**のみを分析しますが、実際の**JSON-LDデータのフィールド名**を理解していませんでした。

### オントロジー vs 実際のデータ

| オントロジー（RDF/Turtle） | 実際のJSON-LDデータ |
|--------------------------|-------------------|
| `mfg:ManufacturingActivity` (クラス) | `"manufacturing_activities"` (配列) |
| `mfg:hasEnergyConsumption` (プロパティ) | `"energy_consumptions"` (配列) |
| `mfg:activityName` (プロパティ) | `"activity_name"` (フィールド) |
| `mfg:productName` (プロパティ) | `"product_name"` (フィールド) |

**命名規則の違い:**
- オントロジー: `camelCase` (例: `hasEnergyConsumption`)
- JSON-LD: `snake_case` + 複数形 (例: `energy_consumptions`)

## 修正内容

### 1. AIプロンプトの改善 ✅

`ai_rule_generator.py`のプロンプトを改善し、JSON-LDの命名規則を明示的に説明:

```python
IMPORTANT: JSON-LD Field Naming Convention
- Ontology properties use camelCase (e.g., hasEnergyConsumption, activityName)
- Actual JSON-LD data fields use snake_case (e.g., energy_consumptions, activity_name)
- Array properties are pluralized (e.g., hasEnergyConsumption → energy_consumptions)
```

### 2. 変換例の追加

AIに以下の変換例を提供:
```
hasEnergyConsumption → energy_consumptions (array)
activityName → activity_name
activityId → activity_id
productName → product_name
organizationName → organization_name
```

## 使用方法

### ステップ1: 新しいルールを生成

修正版のAI rule generatorで再度ルールを生成します:

```bash
# SSL証明書エラーがある場合
python ai_rule_generator.py --no-verify-ssl \
    model/source/manufacturing-ontology.ttl \
    model/target/ghg-report-ontology.ttl \
    output/fixed_ai_rules.yaml
```

### ステップ2: 生成されたルールを確認

`output/fixed_ai_rules.yaml`を開いて、以下を確認:

```yaml
transformation_steps:
  - name: transform_activities_to_emissions
    source: "manufacturing_activities"  # ✅ スネークケース
    target: "emissions"
    iteration: true
    substeps:
      - name: transform_energy_to_emission
        source: "$.energy_consumptions"  # ✅ スネークケース + 複数形
        iteration: true
```

### ステップ3: 変換を実行

```bash
python rule_engine.py \
    output/fixed_ai_rules.yaml \
    test_data/source/sample1_small_factory.json \
    output/fixed_output.json
```

### ステップ4: 結果を確認

```bash
cat output/fixed_output.json | jq
```

期待される出力:
```json
{
  "@context": {
    "ghg": "http://example.org/ghg-report#",
    "xsd": "http://www.w3.org/2001/XMLSchema#"
  },
  "@type": "ghg:EmissionReport",
  "reporting_organization": {
    "@type": "ghg:Organization",
    "organization_name": "Acme Manufacturing Ltd"
  },
  "emissions": [
    {
      "@type": "ghg:Scope2Emission",
      "emission_source": "Factory Tokyo Plant 1 - Widget Assembly Line A",
      "co2_amount": 6250.0,
      "energy_type": "electricity",
      "scope": 2
    },
    {
      "@type": "ghg:Scope1Emission",
      "emission_source": "Factory Tokyo Plant 1 - Widget Assembly Line A",
      "co2_amount": 1725.5,
      "energy_type": "natural_gas",
      "scope": 1
    },
    ...
  ],
  "total_scope_1": 1725.5,
  "total_scope_2": 10450.0,
  "total_emissions": 12175.5
}
```

## トラブルシューティング

### 問題: 出力がまだ空（全てのフィールドが0）

**原因:** 生成されたルールのフィールド名がまだ正しくない可能性があります。

**確認方法:**

```bash
# 生成されたルールのtransformation_stepsを確認
grep -A 20 "transformation_steps:" output/fixed_ai_rules.yaml
```

**手動修正:**

もしフィールド名がまだキャメルケースの場合、手動で修正:

```yaml
# 間違い ❌
transformation_steps:
  - source: "ManufacturingActivities"
    substeps:
      - source: "$.hasEnergyConsumption"

# 正しい ✅
transformation_steps:
  - source: "manufacturing_activities"
    substeps:
      - source: "$.energy_consumptions"
```

### 問題: SSL証明書エラー

```bash
python ai_rule_generator.py --no-verify-ssl [options]
```

### 問題: APIキーが設定されていない

```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

## 参考: 正しいYAMLルールの例

手作りの`transformation_rules.yaml`は正しい例です:

```yaml
transformation_steps:
  - name: "transform_activities_to_emissions"
    source: "manufacturing_activities"  # JSON-LDフィールド名
    target: "emissions"
    iteration: true
    substeps:
      - name: "transform_energy_to_emission"
        source: "$.energy_consumptions"  # JSON-LDフィールド名
        iteration: true
        mapping:
          - target: "co2_amount"
            calculation: "calculate_co2_emission"
```

## まとめ

1. ✅ AI rule generatorのプロンプトを改善（完了）
2. 🔄 新しいルールを生成（ユーザー作業）
3. 🔄 生成されたルールを確認・必要に応じて手動修正（ユーザー作業）
4. 🔄 変換を実行して結果を確認（ユーザー作業）

もし問題が続く場合は、手作りの`transformation_rules.yaml`を参考にして手動でルールを作成することも可能です。
