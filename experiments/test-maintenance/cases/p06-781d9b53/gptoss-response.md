DECISION: fix_production
```diff
--- a/src/Markdig/Extensions/GenericAttributes/GenericAttributesParser.cs
+++ b/src/Markdig/Extensions/GenericAttributes/GenericAttributesParser.cs
@@
-            while (true)
-            {
-                if (c == '}')
-                {
-                    isValid = true;
-                    line.SkipChar(); // skip }
-                    break;
-                }
-
-                if (c == '\0')
-                {
-                    break;
-                }
-
-                bool isClass = c == '.';
-                if (c == '#' || isClass)
-                {
-                    c = line.NextChar(); // Skip #
-                    var start = line.Start;
-                    // Get all non-whitespace characters following a #
-                    // But stop if we found a } or \0
-                    while (c != '}' && !c.IsWhiteSpaceOrZero())
-                    {
-                        c = line.NextChar();
-                    }
-                    var end = line.Start - 1;
-                    if (end == start)
-                    {
-                        break;
-                    }
-                    var text = slice.Text.Substring(start, end - start + 1);
+            while (true)
+            {
+                if (c == '}')
+                {
+                    isValid = true;
+                    line.SkipChar(); // skip }
+
+                    // Skip a trailing line break (and optional carriage return) after the attribute block.
+                    // This prevents a stray newline from being emitted as whitespace inside the following block.
+                    if (line.CurrentChar == '\r')
+                    {
+                        line.SkipChar();
+                        if (line.CurrentChar == '\n')
+                        {
+                            line.SkipChar();
+                        }
+                    }
+                    else if (line.CurrentChar == '\n')
+                    {
+                        line.SkipChar();
+                    }
+
+                    break;
+                }
+
+                if (c == '\0')
+                {
+                    break;
+                }
+
+                bool isClass = c == '.';
+                if (c == '#' || isClass)
+                {
+                    c = line.NextChar(); // Skip #
+                    var start = line.Start;
+                    // Get all non-whitespace characters following a #
+                    // But stop if we found a } or \0
+                    while (c != '}' && !c.IsWhiteSpaceOrZero())
+                    {
+                        c = line.NextChar();
+                    }
+                    var end = line.Start - 1;
+                    if (end == start)
+                    {
+                        break;
+                    }
+                    var text = slice.Text.Substring(start, end - start + 1);
```