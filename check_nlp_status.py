#!/usr/bin/env python3
"""
Diagnostic script to check NLP pipeline status
"""
import sys
from pathlib import Path

print("=" * 60)
print("🔍 SmartGrowth AI — NLP Pipeline Diagnostic")
print("=" * 60)

# Check artifact files
artifact_dir = Path(__file__).parent / "ml_models" / "nlp" / "artifacts"
print("\n📁 Artifact Directory:", artifact_dir)
print("  Exists:", artifact_dir.exists())

if artifact_dir.exists():
    files = list(artifact_dir.glob("*"))
    print(f"  Files found: {len(files)}")
    for f in files:
        if f.is_file():
            size = f.stat().st_size / 1024
            print(f"    - {f.name} ({size:.1f} KB)")
        else:
            subfiles = list(f.glob("*"))
            print(f"    - {f.name}/ ({len(subfiles)} items)")

# Try to load the pipeline
print("\n🔧 Attempting to load NLP pipeline...")
sys.path.insert(0, str(Path(__file__).parent))

try:
    from ml_models.nlp.pipeline import get_nlp_pipeline
    
    pipeline = get_nlp_pipeline()
    print("✅ Pipeline object created")
    
    if pipeline.search_engine is None:
        print("❌ Search engine is None")
    else:
        print("✅ Search engine exists")
        stats = pipeline.search_engine.get_index_stats()
        print(f"   Backend: {stats.get('backend', 'unknown')}")
        print(f"   Document count: {stats.get('document_count', 0)}")
        
        is_built = pipeline.search_engine.is_index_built()
        print(f"   Index built: {is_built}")
    
    if pipeline.analyzer is None:
        print("❌ Sentiment analyzer is None")
    else:
        print("✅ Sentiment analyzer exists")
        print(f"   Backend: {pipeline.analyzer.backend}")
    
    stats = pipeline.get_stats()
    if stats:
        print(f"✅ Stats available: {len(stats)} metrics")
    else:
        print("❌ No stats available")
        
except Exception as e:
    print(f"❌ Error loading pipeline: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("💡 Next steps:")
print("  1. If everything is ✅, restart your API server")
print("  2. If anything is ❌, run: python -m ml_models.nlp.pipeline")
print("=" * 60)
