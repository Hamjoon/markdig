DECISION: fix_production
```diff
--- a/src/Markdig/Extensions/DefinitionLists/DefinitionListParser.cs
+++ b/src/Markdig/Extensions/DefinitionLists/DefinitionListParser.cs
@@
-        var definitionItem = new DefinitionItem(this)
-        {
-            Line = processor.LineIndex,
-            Column = column,
-            Span = new SourceSpan(paragraphBlock.Span.Start, processor.Line.End),
-            OpeningCharacter = processor.CurrentChar,
-        };
+        // The start position of the definition item should be the first non‑space character
+        // after the ':' marker (the column that was calculated earlier in the parser).
+        // Using the paragraph block's start position caused the definition item span to
+        // incorrectly begin at the start of the term line (index 0). We now compute the
+        // correct start position based on the column where the definition content begins.
+        int spanStart = processor.GetSourcePosition(column, out _, out _);
+        var definitionItem = new DefinitionItem(this)
+        {
+            Line = processor.LineIndex,
+            Column = column,
+            Span = new SourceSpan(spanStart, processor.Line.End),
+            OpeningCharacter = processor.CurrentChar,
+        };
```