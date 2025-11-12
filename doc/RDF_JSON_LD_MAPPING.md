# RDFオントロジーとJSON-LDインスタンスの対応ルール

## 概要

このドキュメントは、RDF/Turtleで定義されたオントロジー（`model/`ディレクトリ）と、実際のJSON-LDインスタンスデータ（`test_data/`ディレクトリ）の対応関係を詳細に説明します。

この対応ルールを理解することは、以下の理由で重要です：
- **手動でのデータ作成**: オントロジーに準拠したJSONデータを作成
- **変換ルール作成**: 正確な変換ルールの設計
- **AI生成の検証**: AI生成されたルールやデータの正確性確認
- **データ検証**: インスタンスデータがオントロジーに準拠しているか確認

---

## 1. 命名規則の対応

### 1.1 クラス名の変換

#### オントロジー（RDF/Turtle）
```turtle
mfg:ManufacturingActivity a owl:Class
```

#### JSON-LDインスタンス
```json
{
  "@type": "mfg:ManufacturingActivity",
  ...
}
```

**ルール:**
- オントロジーのクラス名: `PascalCase`（例: `ManufacturingActivity`）
- JSON-LD `@type`: プレフィックス付きで完全に同じ（例: `"mfg:ManufacturingActivity"`）
- 名前空間プレフィックスは`@context`で定義

### 1.2 プロパティ名の変換

#### オントロジー（RDF/Turtle）
```turtle
mfg:activityId a owl:DatatypeProperty
mfg:activityName a owl:DatatypeProperty
mfg:hasEnergyConsumption a owl:ObjectProperty
```

#### JSON-LDインスタンス
```json
{
  "activity_id": "ACT-2024-001",
  "activity_name": "Widget Assembly Line A",
  "energy_consumptions": [...]
}
```

**変換ルール:**

| オントロジー（camelCase） | JSON-LD（snake_case） | 備考 |
|------------------------|---------------------|------|
| `activityId` | `activity_id` | スネークケースに変換 |
| `activityName` | `activity_name` | スネークケースに変換 |
| `productName` | `product_name` | スネークケースに変換 |
| `hasEnergyConsumption` | `energy_consumptions` | スネークケース + 複数形 |
| `energyType` | `energy_type` | スネークケースに変換 |
| `energyTypeName` | `name` | オブジェクト内でシンプル化 |

**パターン:**
1. **camelCaseからsnake_caseへ変換**
   - 大文字の前にアンダースコアを挿入
   - すべて小文字に変換
   - 例: `activityId` → `activity_id`

2. **ObjectPropertyの配列化**
   - `has` + 名前 → 複数形の配列
   - 例: `hasEnergyConsumption` → `energy_consumptions`

3. **ネストされたオブジェクトでのシンプル化**
   - `energyTypeName` → `name`（`energy_type`オブジェクト内）
   - コンテキストで明確な場合は冗長な部分を省略

---

## 2. データ構造の対応

### 2.1 基本パターン

#### パターン1: DatatypeProperty（データ型プロパティ）

**オントロジー定義:**
```turtle
mfg:activityId a owl:DatatypeProperty ;
    rdfs:domain mfg:ManufacturingActivity ;
    rdfs:range xsd:string .
```

**JSON-LDインスタンス:**
```json
{
  "@type": "mfg:ManufacturingActivity",
  "activity_id": "ACT-2024-001"
}
```

**ルール:**
- プロパティ名はsnake_caseに変換
- 値は`rdfs:range`で指定された型に準拠
  - `xsd:string` → JSON文字列
  - `xsd:decimal` → JSON数値
  - `xsd:date` → ISO 8601形式の文字列

#### パターン2: ObjectProperty（オブジェクトプロパティ）- 単一

**オントロジー定義:**
```turtle
mfg:produces a owl:ObjectProperty ;
    rdfs:domain mfg:ManufacturingActivity ;
    rdfs:range mfg:Product .

mfg:Product a owl:Class .
```

**JSON-LDインスタンス:**
```json
{
  "@type": "mfg:ManufacturingActivity",
  "produces": {
    "@type": "mfg:Product",
    "product_name": "Standard Widget",
    "quantity": 5000,
    "unit": "pieces"
  }
}
```

**ルール:**
- プロパティ名はsnake_caseに変換
- 値はネストされたオブジェクト
- オブジェクトは`@type`を持つ
- `@type`は`rdfs:range`で指定されたクラス

#### パターン3: ObjectProperty - 配列（1対多）

**オントロジー定義:**
```turtle
mfg:hasEnergyConsumption a owl:ObjectProperty ;
    rdfs:domain mfg:ManufacturingActivity ;
    rdfs:range mfg:EnergyConsumption .
```

**JSON-LDインスタンス:**
```json
{
  "@type": "mfg:ManufacturingActivity",
  "energy_consumptions": [
    {
      "@type": "mfg:EnergyConsumption",
      "energy_type": {...},
      "amount": 12500,
      "unit": "kWh"
    },
    {
      "@type": "mfg:EnergyConsumption",
      "energy_type": {...},
      "amount": 850,
      "unit": "m³"
    }
  ]
}
```

**ルール:**
- プロパティ名: `has` + 名前 → 複数形の配列名
  - `hasEnergyConsumption` → `energy_consumptions`
  - `hasEmission` → `emissions`
- 値は配列
- 各要素は`@type`を持つオブジェクト

---

## 3. 具体的な対応例

### 3.1 製造オントロジー（Source）

#### オントロジー階層
```
ManufacturingActivity
├── activityId: string
├── activityName: string
├── facility: string
├── startDate: date
├── endDate: date
├── produces: Product
│   ├── productName: string
│   ├── quantity: decimal
│   └── unit: string
└── hasEnergyConsumption: EnergyConsumption[]
    ├── energyType: EnergyType
    │   └── energyTypeName: string
    ├── amount: decimal
    └── unit: string
```

#### JSON-LD構造
```json
{
  "@context": {
    "mfg": "http://example.org/manufacturing#",
    "xsd": "http://www.w3.org/2001/XMLSchema#"
  },
  "manufacturing_activities": [
    {
      "@type": "mfg:ManufacturingActivity",
      "activity_id": "ACT-2024-001",
      "activity_name": "Widget Assembly Line A",
      "facility": "Factory Tokyo Plant 1",
      "start_date": "2024-01-01",
      "end_date": "2024-01-31",
      "produces": {
        "@type": "mfg:Product",
        "product_name": "Standard Widget",
        "quantity": 5000,
        "unit": "pieces"
      },
      "energy_consumptions": [
        {
          "@type": "mfg:EnergyConsumption",
          "energy_type": {
            "@type": "mfg:EnergyType",
            "name": "electricity"
          },
          "amount": 12500,
          "unit": "kWh"
        }
      ]
    }
  ]
}
```

**対応表:**

| オントロジープロパティ | JSON-LDフィールド | 型 | 備考 |
|---------------------|-----------------|-----|------|
| `mfg:activityId` | `activity_id` | string | スネークケース |
| `mfg:activityName` | `activity_name` | string | スネークケース |
| `mfg:facility` | `facility` | string | そのまま |
| `mfg:startDate` | `start_date` | date | スネークケース |
| `mfg:endDate` | `end_date` | date | スネークケース |
| `mfg:produces` | `produces` | object | そのまま |
| `mfg:productName` | `product_name` | string | スネークケース |
| `mfg:quantity` | `quantity` | decimal | そのまま |
| `mfg:unit` | `unit` | string | そのまま |
| `mfg:hasEnergyConsumption` | `energy_consumptions` | array | 複数形 |
| `mfg:energyType` | `energy_type` | object | スネークケース |
| `mfg:energyTypeName` | `name` | string | シンプル化 |
| `mfg:amount` | `amount` | decimal | そのまま |

### 3.2 GHG排出レポートオントロジー（Target）

#### オントロジー階層
```
EmissionReport
├── reportId: string
├── reportingPeriod: string
├── reportDate: date
├── reportingOrganization: Organization
│   └── organizationName: string
├── hasEmission: Emission[]
│   ├── emissionSource: string
│   ├── sourceCategory: string
│   ├── co2Amount: decimal
│   ├── calculationMethod: string
│   └── emissionFactor: decimal
├── totalScope1: decimal
├── totalScope2: decimal
└── totalEmissions: decimal
```

#### JSON-LD構造
```json
{
  "@context": {
    "ghg": "http://example.org/ghg-report#",
    "xsd": "http://www.w3.org/2001/XMLSchema#"
  },
  "@type": "ghg:EmissionReport",
  "report_id": "GHG-AML-2024-01",
  "reporting_period": "2024-01",
  "report_date": "2025-11-12",
  "reporting_organization": {
    "@type": "ghg:Organization",
    "organization_name": "Acme Manufacturing Ltd"
  },
  "emissions": [
    {
      "@type": "ghg:Scope2Emission",
      "emission_source": "Factory Tokyo Plant 1 - Widget Assembly Line A",
      "source_category": "electricity",
      "co2_amount": 6250.0,
      "calculation_method": "Activity-based calculation...",
      "emission_factor": 0.5
    }
  ],
  "total_scope1": 1725.5,
  "total_scope2": 10450.0,
  "total_emissions": 12175.5
}
```

**対応表:**

| オントロジープロパティ | JSON-LDフィールド | 型 | 備考 |
|---------------------|-----------------|-----|------|
| `ghg:reportId` | `report_id` | string | スネークケース |
| `ghg:reportingPeriod` | `reporting_period` | string | スネークケース |
| `ghg:reportDate` | `report_date` | date | スネークケース |
| `ghg:reportingOrganization` | `reporting_organization` | object | スネークケース |
| `ghg:organizationName` | `organization_name` | string | スネークケース |
| `ghg:hasEmission` | `emissions` | array | 複数形 |
| `ghg:emissionSource` | `emission_source` | string | スネークケース |
| `ghg:sourceCategory` | `source_category` | string | スネークケース |
| `ghg:co2Amount` | `co2_amount` | decimal | スネークケース |
| `ghg:calculationMethod` | `calculation_method` | string | スネークケース |
| `ghg:emissionFactor` | `emission_factor` | decimal | スネークケース |
| `ghg:totalScope1` | `total_scope1` | decimal | スネークケース |
| `ghg:totalScope2` | `total_scope2` | decimal | スネークケース |
| `ghg:totalEmissions` | `total_emissions` | decimal | スネークケース |

---

## 4. 特殊なケース

### 4.1 サブクラスの扱い

**オントロジー定義:**
```turtle
ghg:Emission a owl:Class .

ghg:Scope1Emission a owl:Class ;
    rdfs:subClassOf ghg:Emission .

ghg:Scope2Emission a owl:Class ;
    rdfs:subClassOf ghg:Emission .
```

**JSON-LDインスタンス:**
```json
{
  "emissions": [
    {
      "@type": "ghg:Scope1Emission"
    },
    {
      "@type": "ghg:Scope2Emission"
    }
  ]
}
```

**ルール:**
- `@type`には具体的なサブクラスを指定
- 基底クラス（`ghg:Emission`）は使用しない
- 配列は異なるサブクラスのインスタンスを混在可能

### 4.2 ルートレベルの配列

**オントロジー:**
```turtle
# ManufacturingActivityクラスの定義のみ
# 配列化はオントロジーに定義されない
```

**JSON-LDインスタンス:**
```json
{
  "@context": {...},
  "manufacturing_activities": [
    {...},
    {...}
  ]
}
```

**ルール:**
- ルートレベルの配列名は複数形
- オントロジーには配列プロパティとして定義されていない
- 実装上の便宜として配列化

### 4.3 追加フィールド（オントロジー外）

**JSON-LDインスタンス:**
```json
{
  "organization": {
    "name": "Acme Manufacturing Ltd"
  }
}
```

**ルール:**
- `organization`はオントロジーで定義されていない
- JSON-LD仕様では追加フィールドは許容
- 変換時に無視するか、別のルールで処理

### 4.4 ネストされたオブジェクト内のプロパティ名

**オントロジー:**
```turtle
mfg:energyTypeName a owl:DatatypeProperty ;
    rdfs:domain mfg:EnergyType .
```

**JSON-LDインスタンス:**
```json
{
  "energy_type": {
    "@type": "mfg:EnergyType",
    "name": "electricity"  // energyTypeNameではなくname
  }
}
```

**ルール:**
- ネストされたオブジェクト内では冗長な部分を省略
- `energyTypeName` → `name`（`energy_type`内のため）
- コンテキストで明確な場合は短縮形を使用

---

## 5. データ型の対応

### 5.1 XSDからJSONへの型マッピング

| XSD型 | JSON型 | 例 | 備考 |
|-------|--------|-----|------|
| `xsd:string` | string | `"ACT-2024-001"` | 引用符で囲む |
| `xsd:decimal` | number | `12500` | 整数も小数もnumber型 |
| `xsd:integer` | number | `5000` | 整数 |
| `xsd:date` | string | `"2024-01-01"` | ISO 8601形式 |
| `xsd:dateTime` | string | `"2024-01-01T00:00:00Z"` | ISO 8601形式 |
| `xsd:boolean` | boolean | `true`, `false` | 小文字 |

### 5.2 例

**オントロジー:**
```turtle
mfg:startDate a owl:DatatypeProperty ;
    rdfs:range xsd:date .

mfg:quantity a owl:DatatypeProperty ;
    rdfs:range xsd:decimal .
```

**JSON-LD:**
```json
{
  "start_date": "2024-01-01",
  "quantity": 5000
}
```

---

## 6. 実践的なガイドライン

### 6.1 JSONデータ作成時のチェックリスト

1. **@contextの確認**
   - [ ] 必要な名前空間がすべて定義されているか
   - [ ] プレフィックスがオントロジーと一致しているか

2. **@typeの確認**
   - [ ] すべてのオブジェクトに`@type`が設定されているか
   - [ ] クラス名がオントロジーと完全に一致しているか（大文字小文字含む）

3. **プロパティ名の確認**
   - [ ] camelCaseからsnake_caseに変換されているか
   - [ ] 配列プロパティは複数形になっているか
   - [ ] ネストされたオブジェクト内で冗長な部分が省略されているか

4. **データ型の確認**
   - [ ] 文字列は引用符で囲まれているか
   - [ ] 数値は引用符なしか
   - [ ] 日付はISO 8601形式か

5. **構造の確認**
   - [ ] ObjectPropertyは適切にネストされているか
   - [ ] 配列が必要な箇所は配列になっているか

### 6.2 オントロジーからJSONへの変換手順

**ステップ1: クラスの確認**
```turtle
mfg:ManufacturingActivity a owl:Class .
```
↓
```json
{
  "@type": "mfg:ManufacturingActivity"
}
```

**ステップ2: DatatypePropertyの追加**
```turtle
mfg:activityId a owl:DatatypeProperty ;
    rdfs:domain mfg:ManufacturingActivity ;
    rdfs:range xsd:string .
```
↓
```json
{
  "@type": "mfg:ManufacturingActivity",
  "activity_id": "ACT-2024-001"
}
```

**ステップ3: ObjectPropertyの追加**
```turtle
mfg:produces a owl:ObjectProperty ;
    rdfs:domain mfg:ManufacturingActivity ;
    rdfs:range mfg:Product .
```
↓
```json
{
  "@type": "mfg:ManufacturingActivity",
  "activity_id": "ACT-2024-001",
  "produces": {
    "@type": "mfg:Product"
  }
}
```

**ステップ4: 配列ObjectPropertyの追加**
```turtle
mfg:hasEnergyConsumption a owl:ObjectProperty ;
    rdfs:domain mfg:ManufacturingActivity ;
    rdfs:range mfg:EnergyConsumption .
```
↓
```json
{
  "@type": "mfg:ManufacturingActivity",
  "activity_id": "ACT-2024-001",
  "energy_consumptions": [
    {
      "@type": "mfg:EnergyConsumption"
    }
  ]
}
```

### 6.3 よくある間違いと修正方法

#### 間違い1: プロパティ名がcamelCaseのまま ❌
```json
{
  "activityId": "ACT-2024-001"  // ❌
}
```
**修正:** ✅
```json
{
  "activity_id": "ACT-2024-001"  // ✅
}
```

#### 間違い2: 配列プロパティが単数形 ❌
```json
{
  "energy_consumption": [...]  // ❌
}
```
**修正:** ✅
```json
{
  "energy_consumptions": [...]  // ✅
}
```

#### 間違い3: @typeにプレフィックスがない ❌
```json
{
  "@type": "ManufacturingActivity"  // ❌
}
```
**修正:** ✅
```json
{
  "@type": "mfg:ManufacturingActivity"  // ✅
}
```

#### 間違い4: 数値が文字列になっている ❌
```json
{
  "amount": "12500"  // ❌
}
```
**修正:** ✅
```json
{
  "amount": 12500  // ✅
}
```

---

## 7. 変換ルール作成への応用

### 7.1 フィールドマッピング

**オントロジー対応:**
```yaml
field_mappings:
  # organization.nameはオントロジー外だが、JSONデータに存在
  - source_path: "organization.name"
    target_path: "reporting_organization.organization_name"
```

**注意点:**
- SourceとTargetでプロパティ名は異なる可能性がある
- 両方ともsnake_caseを使用

### 7.2 Transformation Steps

**配列の反復処理:**
```yaml
transformation_steps:
  - name: "transform_activities_to_emissions"
    source: "manufacturing_activities"  # 配列（複数形）
    target: "emissions"                 # 配列（複数形）
    iteration: true
    substeps:
      - name: "transform_energy_to_emission"
        source: "$.energy_consumptions"  # ネストされた配列（複数形）
        iteration: true
```

**ルール:**
- 配列フィールド名は複数形を使用
- JSONPathで配列を参照（`$.energy_consumptions`）

---

## 8. まとめ

### 8.1 核心となるルール

1. **命名規則:**
   - オントロジー: `camelCase`
   - JSON-LD: `snake_case`

2. **配列化:**
   - `has` + 名前 → 複数形
   - 例: `hasEnergyConsumption` → `energy_consumptions`

3. **型変換:**
   - XSD型 → JSON型（適切に変換）

4. **構造:**
   - ObjectProperty → ネストされたオブジェクト
   - 1対多 → 配列

### 8.2 重要なポイント

- **オントロジーは抽象的な定義**: クラスとプロパティの関係を定義
- **JSON-LDは具体的なデータ**: 実際のインスタンスデータ
- **命名規則の変換が必須**: camelCase ⇄ snake_case
- **配列の扱いに注意**: オントロジーで明示されない配列化

### 8.3 このドキュメントの活用方法

1. **データ作成**: オントロジーに準拠したJSONデータの作成
2. **検証**: 既存データがオントロジーに準拠しているか確認
3. **変換ルール設計**: 正確なフィールドマッピングの作成
4. **AI生成の評価**: AI生成されたルールやデータの正確性検証

---

## 付録A: 完全な対応例

### 製造活動からGHG排出レポートへの変換

**Source (Manufacturing):**
```json
{
  "@context": {
    "mfg": "http://example.org/manufacturing#"
  },
  "manufacturing_activities": [
    {
      "@type": "mfg:ManufacturingActivity",
      "activity_id": "ACT-2024-001",
      "energy_consumptions": [
        {
          "@type": "mfg:EnergyConsumption",
          "energy_type": {
            "@type": "mfg:EnergyType",
            "name": "electricity"
          },
          "amount": 12500
        }
      ]
    }
  ]
}
```

**Target (GHG Report):**
```json
{
  "@context": {
    "ghg": "http://example.org/ghg-report#"
  },
  "@type": "ghg:EmissionReport",
  "emissions": [
    {
      "@type": "ghg:Scope2Emission",
      "source_category": "electricity",
      "co2_amount": 6250.0
    }
  ]
}
```

**対応関係:**
```
manufacturing_activities[]                    → emissions[]
  └─ energy_consumptions[]
       ├─ energy_type.name = "electricity"    → source_category = "electricity"
       └─ amount = 12500                      → co2_amount = 6250.0
                                                 (計算: 12500 × 0.5)
```

---

## 付録B: 参考ファイル

- **オントロジー定義:**
  - `model/source/manufacturing-ontology.ttl`
  - `model/target/ghg-report-ontology.ttl`

- **インスタンスデータ:**
  - `test_data/source/sample1_small_factory.json`
  - `test_data/source/sample2_multi_fuel.json`
  - `test_data/source/sample3_electronics.json`

- **変換結果:**
  - `output/correct_output.json`
  - `test_data/target/output1_small_factory.json`

- **変換ルール:**
  - `transformation_rules.yaml` - 手作りの正しいルール

---

**作成日:** 2025-11-12
**バージョン:** 1.0
**更新履歴:** 初版作成
