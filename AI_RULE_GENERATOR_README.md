# AI-Powered Rule Generator

AIを活用してオントロジーから賢い変換ルールを自動生成します。

## 概要

`ai_rule_generator.py` は Claude AI を使用して、2つのオントロジーを分析し、以下を自動生成します：

1. **クラスマッピング** - セマンティックな理解に基づく対応付け
2. **プロパティマッピング** - 詳細なフィールド対応
3. **計算ルール** - 必要な計算式（例: CO2排出量 = 燃料量 × 排出係数）
4. **集計ルール** - 配列データの合計、平均、カウントなど
5. **変換ステップ** - 実行順序を含む完全な変換パイプライン

## 従来の rule_generator.py との違い

| 機能 | rule_generator.py<br>(単純なマッチング) | ai_rule_generator.py<br>(AI分析) |
|------|----------------------------------------|----------------------------------|
| クラス対応付け | 名前の類似度のみ | セマンティックな理解 |
| プロパティ対応 | 名前の類似度のみ | 意味に基づく対応 |
| 計算の推論 | ❌ なし | ✅ 自動推論 |
| 集計の推論 | ❌ なし | ✅ 自動推論 |
| 定数テーブル | ❌ なし | ✅ 自動提案 |
| 精度 | 低～中 | 高 |

## セットアップ

### 1. 必要なライブラリのインストール

```bash
pip install anthropic pyyaml rdflib
```

### 2. API キーの設定

Anthropic API キーを環境変数に設定：

```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

または、直接コマンドライン引数で指定：

```bash
python ai_rule_generator.py source.ttl target.ttl output.yaml your-api-key
```

## 使用方法

### 基本的な使い方

```bash
python ai_rule_generator.py \
    model_examples/vehicle_fleet/vehicle-fleet-ontology.ttl \
    model_examples/vehicle_fleet/fleet-emissions-ontology.ttl \
    ai_generated_rules.yaml
```

### 出力例

```
======================================================================
AI ANALYSIS IN PROGRESS
======================================================================
Analyzing ontologies with Claude AI...
Source: http://example.org/fleet#
Target: http://example.org/fleet-emissions#

======================================================================
AI ANALYSIS COMPLETE
======================================================================

======================================================================
AI TRANSFORMATION SUGGESTIONS
======================================================================

📋 CLASS MAPPINGS:
  ✓ Vehicle → VehicleEmission
    Confidence: 95%
    Reasoning: Vehicle represents a fleet vehicle, which generates emissions.
               The target VehicleEmission captures these emissions.

  ✓ Organization → ReportingOrganization
    Confidence: 90%
    Reasoning: Both represent the organization operating the fleet

📋 PROPERTY MAPPINGS:

  For Vehicle → VehicleEmission:
    → vehicleId → vehicle_id (direct)
    → vehicleType → vehicle_type (direct)
    🔢 fuelConsumptions → fuel_consumed (aggregation)
       Need to sum fuel amounts from all consumption records
    🔢 fuelConsumptions → carbon_emissions (calculation)
       Calculate total CO2 by summing (fuel_amount × emission_factor)

🔢 CALCULATIONS:
  • calculate_vehicle_emissions: Calculate total CO2 emissions from fuel
    Formula: sum(fuel_amount * emission_factor for each fuel_consumption)
    Inputs: fuel_consumptions, emission_factors
    Reasoning: CO2 emissions must be calculated from fuel consumption
               using standard emission factors

📊 AGGREGATIONS:
  • sum_fuel_consumed: Total fuel consumed by vehicle
    Function: sum(fuel_amount)
    Source: Vehicle.fuel_consumptions
    Target: fuel_consumed

  • sum_distance: Total distance traveled
    Function: sum(distance_traveled)
    Source: Vehicle.fuel_consumptions
    Target: distance_traveled

📚 LOOKUP TABLES:
  • fuel_emission_factors: CO2 emission factors by fuel type
    Examples: {"diesel": 2.68, "gasoline": 2.31, "lpg": 1.51}

🔄 TRANSFORMATION STEPS:
  1. transform_vehicles_to_emissions
     Transform each vehicle to an emission record
     vehicles → vehicle_emissions

  2. calculate_aggregations
     Calculate fleet-wide totals
     vehicle_emissions → total_emissions, total_fuel, vehicle_count

======================================================================

✅ AI-generated rules saved to: ai_generated_rules.yaml
```

## 生成されるルールの構造

AIが生成するYAMLルールは、以下のセクションを含みます：

```yaml
metadata:
  name: "AI-Generated Transformation"
  version: "1.0"
  generated_by: "AI"
  ai_model: "claude-sonnet-4"

constants:
  # AIが推論した定数とルックアップテーブル
  fuel_emission_factors:
    diesel: 2.68
    gasoline: 2.31

field_mappings:
  # シンプルなフィールド対応
  - source_path: vehicle_id
    target_path: vehicle_id

calculation_rules:
  # AIが推論した計算ルール
  - name: calculate_vehicle_emissions
    description: "Calculate CO2 from fuel consumption"
    formula: "fuel_amount * emission_factor"
    inputs: [...]

transformation_steps:
  # 実行順序を含む変換ステップ
  - name: transform_vehicles
    source: vehicles
    target: vehicle_emissions
    iteration: true
    substeps: [...]

  - name: calculate_aggregations
    aggregations:
      - function: sum
        field: carbon_emissions
        target: total_emissions
```

## Python API

プログラムから使用する場合：

```python
from ai_rule_generator import AIRuleGenerator

# 初期化
generator = AIRuleGenerator(
    "source_ontology.ttl",
    "target_ontology.ttl",
    api_key="your-api-key"  # オプション、環境変数を使う場合は不要
)

# AI分析を実行
suggestions = generator.analyze_with_ai()

# 提案を表示
generator.display_suggestions()

# ルールを生成して保存
generator.save_rules("output_rules.yaml")

# または、直接ルールを取得
rules_dict = generator.generate_rules()
```

## 利点

### 1. セマンティック理解
単純な名前マッチングではなく、概念の意味を理解：
- "Vehicle" と "VehicleEmission" の関係を理解
- "FuelConsumption" から "carbon_emissions" への計算が必要だと推論

### 2. 計算の自動推論
ドメイン知識に基づいて計算を推論：
- 燃料消費 × 排出係数 = CO2排出量
- 距離と燃料から燃費を計算

### 3. 集計の自動推論
配列データから必要な集計を識別：
- 複数の燃料消費記録を合計
- 車両ごとの総距離を計算

### 4. 定数テーブルの提案
変換に必要な定数を自動提案：
- 燃料タイプごとの排出係数
- 単位変換係数

### 5. 実行可能なルール
生成されたルールは即座に `rule_engine.py` で実行可能

## 制限事項

1. **API キーが必要**: Anthropic API キー（有料）が必要
2. **API コスト**: 大きなオントロジーでは複数回の API 呼び出しが必要な場合がある
3. **精度**: AIの推論は100%正確ではない。生成されたルールの確認が推奨
4. **複雑なロジック**: 非常に複雑なビジネスロジックは手動調整が必要な場合がある

## トラブルシューティング

### API キーエラー
```
ValueError: ANTHROPIC_API_KEY environment variable or api_key parameter required
```
→ API キーを設定してください

### JSON パースエラー
```
Error parsing AI response: ...
```
→ AIの応答が想定形式でない場合。再試行するか、ログを確認

### オントロジー読み込みエラー
```
Error parsing ontology: ...
```
→ TTL ファイルの形式を確認してください

## 例

### Vehicle Fleet → Emissions の変換

```bash
python ai_rule_generator.py \
    model_examples/vehicle_fleet/vehicle-fleet-ontology.ttl \
    model_examples/vehicle_fleet/fleet-emissions-ontology.ttl \
    model_examples/vehicle_fleet/ai_rules.yaml

# 生成されたルールで変換を実行
python rule_engine.py \
    model_examples/vehicle_fleet/ai_rules.yaml \
    model_examples/vehicle_fleet/sample_fleet_data.json \
    model_examples/vehicle_fleet/ai_output.json
```

## まとめ

AI-Powered Rule Generator は、従来の単純なマッチングベースのアプローチを超えて、セマンティックな理解に基づいた賢い変換ルール生成を実現します。

特に有効なケース：
- ✅ 複雑な計算が必要な変換
- ✅ 集計やロールアップが必要な変換
- ✅ ドメイン知識が必要な変換
- ✅ プロトタイプやPoCの迅速な作成

手動調整が推奨されるケース：
- ⚠️ ミッションクリティカルなシステム
- ⚠️ 非常に特殊なビジネスロジック
- ⚠️ 100%の精度が必要な場合

両方のアプローチ（AIと手動）を組み合わせることで、最高の結果が得られます。
