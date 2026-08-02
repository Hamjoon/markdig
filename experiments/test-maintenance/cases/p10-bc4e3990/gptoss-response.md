DECISION: fix_production
```diff
--- a/src/Markdig/Parsers/ListBlockParser.cs
+++ b/src/Markdig/Parsers/ListBlockParser.cs
@@
-        // Starts/continue the list unless:
-        // - an empty list item follows a paragraph
-        // - an ordered list is not starting by '1'
-        block ??= state.LastBlock;
-        if (block is not null && block.IsParagraphBlock)
-        {
-            if (state.IsBlankLine ||
-                state.IsOpen(block) && listInfo.BulletType == '1' && listInfo.OrderedStart is not "1")
-            {
-                state.GoToColumn(initColumn);
-                state.TriviaStart = savedTriviaStart; // restore changed TriviaStart state
-                return BlockState.None;
-            }
-        }
+        // Starts/continue the list unless:
+        // - an empty list item follows a paragraph
+        // - an ordered list is not starting by '1' **and** the paragraph is part of a list item
+        //   (this prevents treating a continuation of a list item as a new list)
+        block ??= state.LastBlock;
+        if (block is not null && block.IsParagraphBlock)
+        {
+            // If we are on a blank line we cannot start a new list
+            if (state.IsBlankLine)
+            {
+                state.GoToColumn(initColumn);
+                state.TriviaStart = savedTriviaStart; // restore changed TriviaStart state
+                return BlockState.None;
+            }
+
+            // When the paragraph is inside a ListItemBlock we keep the original restriction:
+            // an ordered list that does not start with '1' should not be started here.
+            // For paragraphs outside of list items (e.g., inside blockquotes) we allow it.
+            if (state.IsOpen(block) &&
+                listInfo.BulletType == '1' && listInfo.OrderedStart is not \"1\" && block.Parent is ListItemBlock)
+            {
+                state.GoToColumn(initColumn);
+                state.TriviaStart = savedTriviaStart; // restore changed TriviaStart state
+                return BlockState.None;
+            }
+        }
```