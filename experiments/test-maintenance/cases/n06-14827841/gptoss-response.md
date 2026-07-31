DECISION: fix_production
```diff
@@
-    public void PopIndent()
-    {
-        if (this.indents.Count > 0)
-            indents.RemoveAt(indents.Count - 1);
-        else
-            throw new InvalidOperationException("No indent to pop");
-    }
+    public void PopIndent()
+    {
+        if (this.indents.Count > 0)
+            indents.RemoveAt(indents.Count - 1);
+        // Previously, PopIndent silently did nothing when there was no indent.
+        // The recent change introduced an exception, which breaks callers that
+        // expect the original tolerant behavior. Restoring the original semantics
+        // ensures compatibility with existing tests and library usage.
+    }
```