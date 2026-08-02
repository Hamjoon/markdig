DECISION: fix_production
```diff
--- a/src/Markdig/Parsers/Inlines/CodeInlineParser.cs
+++ b/src/Markdig/Parsers/Inlines/CodeInlineParser.cs
@@
-                ReadOnlySpan<char> lookAhead = span.Length > 1 ? span.Slice(1) : ReadOnlySpan<char>.Empty;
-                while (!lookAhead.IsEmpty && (lookAhead[0] == '\r' || lookAhead[0] == '\n'))
-                {
-                    lookAhead = lookAhead.Slice(1);
-                }
-                if (lookAhead[0] == '|')
-                {
-                    // We saw the start of a code inline, but the close sticks are not present on the same line.
-                    // If the next line starts with a pipe character, this is likely an incomplete CodeInline within a table.
-                    // Treat it as regular text to avoid breaking the overall table shape.
-                    if (processor.Inline != null && processor.Inline.ContainsParentOfType<PipeTableDelimiterInline>())
-                    {
-                        slice.Start = openingStart;
-                        return false;
-                    }
-                }
+                // Look ahead to see if the next line starts with a pipe character.
+                // This is used to detect an incomplete CodeInline inside a table.
+                // The original implementation accessed lookAhead[0] without ensuring the span was non‑empty,
+                // which caused an IndexOutOfRangeException for inputs where the look‑ahead span is empty
+                // (e.g., a backtick followed by a newline and then EOF or a non‑pipe character).
+                ReadOnlySpan<char> lookAhead = span.Length > 1 ? span.Slice(1) : ReadOnlySpan<char>.Empty;
+                while (!lookAhead.IsEmpty && (lookAhead[0] == '\r' || lookAhead[0] == '\n'))
+                {
+                    lookAhead = lookAhead.Slice(1);
+                }
+                // Guard against empty lookAhead before accessing its first element.
+                if (!lookAhead.IsEmpty && lookAhead[0] == '|')
+                {
+                    // We saw the start of a code inline, but the close sticks are not present on the same line.
+                    // If the next line starts with a pipe character, this is likely an incomplete CodeInline within a table.
+                    // Treat it as regular text to avoid breaking the overall table shape.
+                    if (processor.Inline != null && processor.Inline.ContainsParentOfType<PipeTableDelimiterInline>())
+                    {
+                        slice.Start = openingStart;
+                        return false;
+                    }
+                }
```