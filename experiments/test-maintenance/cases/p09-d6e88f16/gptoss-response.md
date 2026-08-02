DECISION: fix_production
```diff
@@
-        if (c == '\n' || c == '\r')
-        {
-            if (!isFirstLineEmpty && !tableState.LineHasPipe)
-            {
-                tableState.IsInvalidTable = true;
-            }
-            tableState.LineHasPipe = false;
-            lineBreakParser.Match(processor, ref slice);
-            tableState.LineIndex++;
-            if (!isFirstLineEmpty)
-            {
-                tableState.ColumnAndLineDelimiters.Add(processor.Inline!);
-                tableState.EndOfLines.Add(processor.Inline!);
-            }
-        }
+        if (c == '\n' || c == '\r')
+        {
+            // If we have already started collecting delimiters for a potential table
+            // (i.e., we have seen at least one pipe delimiter) and the current line
+            // does not contain a pipe, then the table is considered invalid.
+            // The original logic also marked the table as invalid when encountering
+            // the first newline after normal paragraph text, which prevented tables
+            // from being recognized when they start immediately after a paragraph
+            // without a blank line. We now ensure that we only flag the table as
+            // invalid after we have begun processing a table (i.e., when there are
+            // already collected delimiters).
+            if (!isFirstLineEmpty && !tableState.LineHasPipe && tableState.ColumnAndLineDelimiters.Count > 0)
+            {
+                tableState.IsInvalidTable = true;
+            }
+            tableState.LineHasPipe = false;
+            lineBreakParser.Match(processor, ref slice);
+            tableState.LineIndex++;
+            if (!isFirstLineEmpty)
+            {
+                tableState.ColumnAndLineDelimiters.Add(processor.Inline!);
+                tableState.EndOfLines.Add(processor.Inline!);
+            }
+        }
```