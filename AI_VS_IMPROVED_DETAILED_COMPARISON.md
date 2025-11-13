# AI生成 vs 自動生成：詳細な問題分析

## 📊 出力の比較

### ai_output_v2_real.json（AI生成ルール使用）

```json
{
  "emissions": [
    {},  // ❌ 完全に空
    {},  // ❌ 完全に空
    {}   // ❌ 完全に空
  ],
  "total_emissions": 0  // ❌ 計算されない
}
```

### ai_output_v2_improved.json（自動生成ルール使用）

```json
{
  "emissions": [
    {
      "@type": "ghg:Scope2Emission",  // ✅ 正しい型
      "co2_amount": 6250.0,            // ✅ 正しい計算
      "calculation_method": "...",      // ✅ 設定されている
      "emission_factor": {...}          // ✅ 正しい係数
    },
    {
      "@type": "ghg:Scope1Emission",
      "co2_amount": 1725.5,             // ✅ 正しい計算
      ...
    },
    {
      "@type": "ghg:Scope2Emission",
      "co2_amount": 4200.0,             // ✅ 正しい計算
      ...
    }
  ],
  "total_emissions": 12175.5  // ✅ 正しい合計
}
```

**差分:**
- ❌ vs ✅: 空のオブジェクト vs 完全なデータ
- 0 vs 12,175.5: ゼロ vs 正しい排出量

---

## 🔍 根本原因：Substeps構造の違い

### 問題1: `field_mappings` vs `mapping`

#### AI生成（動作しない）

```yaml
substeps:
  - name: iterate_energy_consumptions
    source: $.energy_consumptions
    iteration: true
    substeps:  # ❌ ネストされたsubsteps
      - name: map_emission_fields
        field_mappings:  # ❌ rule_engineは認識しない
          - target: emission_source
            source: $.activity_name
          - target: source_category
            source: $.energy_type.name
```

**問題点:**
1. `field_mappings` キー → rule_engineは `mapping` を期待
2. ネストされたsubsteps → rule_engineは1レベルのネストしかサポートしない

**結果:**
- rule_engineが`field_mappings`を無視
- フィールドマッピングが実行されない
- 空のオブジェクト`{}`が生成される

#### 自動生成（動作する）

```yaml
substeps:
  - name: iterate_energy_consumptions
    source: $.energy_consumptions
    iteration: true
    mapping:  # ✅ rule_engineが認識
      - target: emission_source
        source: $.activity_name
        context: parent
      - target: source_category
        source: $.energy_type.name
      - target: '@type'
        calculation: determine_scope
        format: 'ghg:Scope{scope}Emission'
      - target: co2_amount
        calculation: calculate_co2_emission
      - target: calculation_method
        fixed_value: 'Activity-based calculation using standard emission factors'
      - target: emission_factor
        lookup:
          source: constants.emission_factors
          key: $.energy_type.name
          key_transform: lowercase_underscore
```

**成功要因:**
1. ✅ `mapping` キー → rule_engineが認識
2. ✅ フラットな構造（ネストなし）
3. ✅ すべてのマッピングが1つの配列内
4. ✅ calculation, fixed_value, lookupなどの指示が含まれる

**結果:**
- すべてのフィールドが正しくマッピングされる
- 計算が実行される
- 完全なemissionオブジェクトが生成される

---

## 📋 構造の詳細比較

### AI生成（2レベルのネスト）

```
transform_activities_to_emissions
└── substeps:
    └── iterate_energy_consumptions  ← Level 1
        └── substeps:  ← ❌ Level 2 (rule_engineは処理しない)
            ├── map_emission_fields
            │   └── field_mappings: [...]  ← ❌ 認識されない
            ├── calculate_co2_amount
            │   └── calculation: ...  ← ❌ 孤立している
            └── determine_emission_type
                └── conditional_mapping: ...  ← ❌ 認識されない
```

### 自動生成（1レベルのネスト）

```
transform_activities_to_emissions
└── substeps:
    └── iterate_energy_consumptions  ← Level 1
        └── mapping: [  ← ✅ rule_engineが処理
            {target: emission_source, source: ...},
            {target: source_category, source: ...},
            {target: '@type', calculation: ...},
            {target: co2_amount, calculation: ...},
            {target: calculation_method, fixed_value: ...},
            {target: emission_factor, lookup: ...}
        ]
```

---

## 🔧 具体的な違いの例

### 例1: emission_sourceのマッピング

#### AI生成
```yaml
substeps:
  - name: iterate_energy_consumptions
    substeps:  # ネストレベル2
      - name: map_emission_fields
        field_mappings:  # ❌ 認識されない
          - target: emission_source
            source: $.activity_name
```

**処理:** rule_engineが`field_mappings`を無視 → `emission_source`が設定されない

#### 自動生成
```yaml
substeps:
  - name: iterate_energy_consumptions
    mapping:  # ✅ 認識される
      - target: emission_source
        source: $.activity_name
        context: parent
```

**処理:** rule_engineが`mapping`を処理 → `emission_source`が設定される

---

### 例2: co2_amountの計算

#### AI生成
```yaml
substeps:
  - name: iterate_energy_consumptions
    substeps:
      - name: calculate_co2_amount  # 独立したsubstep
        calculation: calculate_co2_emissions
        inputs:
          amount: $.amount
          energy_type: $.energy_type.name
        output: co2_amount
```

**処理:** rule_engineはネストされた独立した`calculation`を処理できない → 計算されない

#### 自動生成
```yaml
substeps:
  - name: iterate_energy_consumptions
    mapping:
      - target: co2_amount  # mappingの一部
        calculation: calculate_co2_emission
```

**処理:** rule_engineが`mapping`内の`calculation`を処理 → 正しく計算される

---

### 例3: @typeの条件付き設定

#### AI生成
```yaml
substeps:
  - name: iterate_energy_consumptions
    substeps:
      - name: determine_emission_type
        conditional_mapping:  # ❌ rule_engineは認識しない
          field: $.energy_type.name
          mappings:
            electricity:
              '@type': ghg:Scope2Emission
            natural_gas:
              '@type': ghg:Scope1Emission
```

**処理:** `conditional_mapping`はサポートされていない → `@type`が設定されない

#### 自動生成
```yaml
substeps:
  - name: iterate_energy_consumptions
    mapping:
      - target: '@type'
        calculation: determine_scope
        format: 'ghg:Scope{scope}Emission'
```

**処理:** `calculation`で1または2を返し、`format`で文字列化 → 正しく設定される

---

## 📊 問題の影響

| フィールド | AI生成 | 自動生成 | 影響 |
|-----------|--------|----------|------|
| emission_source | ❌ 設定されない | ✅ 設定される | データ品質 |
| source_category | ❌ 設定されない | ✅ 設定される | データ品質 |
| @type | ❌ 設定されない | ✅ 設定される | **クリティカル** |
| co2_amount | ❌ 計算されない | ✅ 計算される | **クリティカル** |
| calculation_method | ❌ 設定されない | ✅ 設定される | メタデータ |
| emission_factor | ❌ 設定されない | ✅ 設定される | メタデータ |

**結果:**
- AI生成: 空のオブジェクト`{}` × 3
- 自動生成: 完全なemissionオブジェクト × 3

---

## 🎯 なぜ自動生成は動作するのか

### 1. rule_engine互換の構造

自動生成ロジック（`_auto_generate_substeps()`）は、rule_engineが実際にサポートする構造を熟知：

```python
def _auto_generate_substeps(self, step: Dict, suggestions: Dict):
    if 'activit' in source and 'emission' in target:
        return [{
            'name': 'iterate_energy_consumptions',
            'source': '$.energy_consumptions',
            'iteration': True,
            'mapping': [  # ← rule_engine互換のキー
                {'target': 'emission_source', 'source': '$.activity_name', 'context': 'parent'},
                {'target': 'source_category', 'source': '$.energy_type.name'},
                {'target': '@type', 'calculation': 'determine_scope'},
                {'target': 'co2_amount', 'calculation': 'calculate_co2_emission'},
                ...
            ]
        }]
```

### 2. フラットな構造

- ✅ 1レベルのsubsteps
- ✅ mappingはsubstepsの直接の子
- ✅ ネストされたsubstepsなし

### 3. 完全なマッピング

すべての必要なフィールドを1つの`mapping`配列に含める：
- 直接マッピング（source）
- 計算（calculation）
- 固定値（fixed_value）
- ルックアップ（lookup）

---

## 💡 解決策

### 現在の実装（ハイブリッドアプローチ）

```python
def _generate_transformation_steps(self, suggestions: Dict):
    ai_substeps = step_info.get('substeps', [])
    if ai_substeps:
        step['substeps'] = ai_substeps  # AIの提案を試す
    else:
        step['substeps'] = self._auto_generate_substeps(step, suggestions)  # フォールバック
```

**問題:** AIが非互換のsubstepsを提供しても、そのまま使用してしまう

### 改善案1: 互換性チェック

```python
def _generate_transformation_steps(self, suggestions: Dict):
    ai_substeps = step_info.get('substeps', [])
    if ai_substeps and self._is_compatible_with_rule_engine(ai_substeps):
        step['substeps'] = ai_substeps
    else:
        step['substeps'] = self._auto_generate_substeps(step, suggestions)

def _is_compatible_with_rule_engine(self, substeps):
    """Check if substeps are compatible with rule_engine."""
    for substep in substeps:
        # Check for nested substeps with field_mappings
        if 'substeps' in substep:
            for nested in substep['substeps']:
                if 'field_mappings' in nested:
                    return False  # Not compatible
        # Check for conditional_mapping
        if 'conditional_mapping' in substep:
            return False
    return True
```

### 改善案2: 正規化

```python
def _normalize_ai_substeps(self, substeps):
    """Convert AI-generated substeps to rule_engine format."""
    normalized = []
    for substep in substeps:
        if 'substeps' in substep and substep.get('iteration'):
            # Flatten nested substeps
            mapping = []
            for nested in substep['substeps']:
                if 'field_mappings' in nested:
                    mapping.extend(nested['field_mappings'])
                elif 'calculation' in nested:
                    mapping.append({
                        'target': nested['output'],
                        'calculation': nested['calculation']
                    })

            substep['mapping'] = mapping
            del substep['substeps']

        normalized.append(substep)
    return normalized
```

---

## 🔬 テストケース

### テスト1: AI生成ルール（現状）

```bash
python rule_engine.py output/ai_generated_rules_v2_real.yaml ...
# Result: Total emissions: 0 kg-CO2 ❌
```

### テスト2: 自動生成ルール（現状）

```bash
python rule_engine.py output/ai_generated_rules_v2_improved.yaml ...
# Result: Total emissions: 12,175.5 kg-CO2 ✅
```

### テスト3: 正規化後（理論）

```bash
# AI生成ルールを正規化してから使用
python normalize_and_transform.py output/ai_generated_rules_v2_real.yaml ...
# Expected: Total emissions: 12,175.5 kg-CO2 ✅
```

---

## 📝 まとめ

### 問題の核心

| 項目 | AI生成 | rule_engine期待 | 互換性 |
|------|--------|----------------|--------|
| **キー名** | `field_mappings` | `mapping` | ❌ |
| **構造** | 2レベルネスト | 1レベルネスト | ❌ |
| **条件マッピング** | `conditional_mapping` | `calculation` + `format` | ❌ |
| **計算** | 独立したsubstep | `mapping`内のエントリ | ❌ |

### なぜ自動生成が成功するのか

1. ✅ rule_engine互換のキー名を使用
2. ✅ フラットな構造（1レベルのネスト）
3. ✅ すべての操作を`mapping`配列に統合
4. ✅ サポートされている指示のみ使用

### 推奨事項

**短期:** 現在のハイブリッドアプローチを継続
- AIが互換性のないsubstepsを提供 → 自動生成にフォールバック
- 確実に動作するルールを生成

**長期:** 以下のいずれかを実装
1. **正規化レイヤー**: AIの出力をrule_engine互換形式に変換
2. **rule_engineの拡張**: `field_mappings`, `conditional_mapping`をサポート
3. **AIプロンプトの改善**: rule_engine互換の構造を生成するよう指示

---

## 🎓 教訓

### AIは素晴らしい提案をするが...

✅ **AIができること:**
- 論理的なマッピングを理解
- 必要な変換を特定
- 詳細なsubstepsを生成

❌ **AIができないこと（現状）:**
- rule_engineの実装詳細を知る
- サポートされているキー名を使用
- 正しいネスト深度を守る

### 自動生成ロジックの価値

✅ **実装知識:**
- rule_engineが実際にサポートする構造
- 正しいキー名
- 適切なネスト深度

✅ **ドメイン知識:**
- manufacturing → GHG変換パターン
- 必須のフィールドマッピング
- 計算とルックアップの統合

**結論:** AIの創造性 + 実装知識 = 完璧なソリューション

---

**作成日:** 2025-11-12
**ステータス:** 詳細分析完了
**推奨:** 現在の実装（ハイブリッド）を継続使用
