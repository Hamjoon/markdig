DECISION: fix_production
```diff
@@
-        bool mayBeValid = span.Length >= 4 && span[0] switch
-        {
-            'h' => span.StartsWith("https://", StringComparison.Ordinal) || span.StartsWith("http://", StringComparison.Ordinal),
-            'w' => span.StartsWith("www.", StringComparison.Ordinal), // We won't match http:/www. or /www.xxx
-            'f' => span.StartsWith("ftp://", StringComparison.Ordinal),
-            'm' => span.StartsWith("mailto:", StringComparison.Ordinal),
-            _ => span.StartsWith("tel:", StringComparison.Ordinal),
-        };
+        // Pre‑check the URL using a case‑insensitive comparison, matching the original
+        // behaviour which accepted schemes like \"HTTP://\" or \"WWW.\"
+        bool mayBeValid = span.Length >= 4 && span[0] switch
+        {
+            'h' => span.StartsWith("https://", StringComparison.OrdinalIgnoreCase) ||
+                   span.StartsWith("http://", StringComparison.OrdinalIgnoreCase),
+            'w' => span.StartsWith("www.", StringComparison.OrdinalIgnoreCase), // We won't match http:/www. or /www.xxx
+            'f' => span.StartsWith("ftp://", StringComparison.OrdinalIgnoreCase),
+            'm' => span.StartsWith("mailto:", StringComparison.OrdinalIgnoreCase),
+            _   => span.StartsWith("tel:", StringComparison.OrdinalIgnoreCase),
+        };
```