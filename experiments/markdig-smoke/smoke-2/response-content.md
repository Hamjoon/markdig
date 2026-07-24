DECISION: fix_production
diff --git a/src/Markdig/Helpers/LinkHelper.cs b/src/Markdig/Helpers/LinkHelper.cs
index b744bed8..d3f9a2c1 100644
--- a/src/Markdig/Helpers/LinkHelper.cs
+++ b/src/Markdig/Helpers/LinkHelper.cs
@@
-            // Handle German and Scandinavian characters explicitly when ASCII-only output is requested.
-            ReadOnlySpan<char> normalized;
-            if (allowOnlyAscii && IsSpecialScandinavianOrGermanChar(c))
-            {
-                normalized = NormalizeScandinavianOrGermanChar(c);
-            }
-            else
-            {
-                normalized = allowOnlyAscii ? CharNormalizer.ConvertToAscii(c) : ReadOnlySpan<char>.Empty;
-            }
+            // Handle German and Scandinavian characters explicitly (always). When allowOnlyAscii is true,
+            // these characters are expanded to their ASCII equivalents (e.g., ö → oe). When allowOnlyAscii
+            // is false, they are also expanded, matching the original behavior expected by the tests.
+            ReadOnlySpan<char> normalized;
+            if (IsSpecialScandinavianOrGermanChar(c))
+            {
+                normalized = NormalizeScandinavianOrGermanChar(c);
+            }
+            else
+            {
+                normalized = allowOnlyAscii ? CharNormalizer.ConvertToAscii(c) : ReadOnlySpan<char>.Empty;
+            }