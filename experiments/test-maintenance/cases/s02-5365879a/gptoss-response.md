DECISION: fix_production
diff --git a/src/Markdig/Extensions/Abbreviations/AbbreviationParser.cs b/src/Markdig/Extensions/Abbreviations/AbbreviationParser.cs
index e3855cc3..b7f2a1d4 100644
--- a/src/Markdig/Extensions/Abbreviations/AbbreviationParser.cs
+++ b/src/Markdig/Extensions/Abbreviations/AbbreviationParser.cs
@@
-        foreach (var leaf in inlineProcessor.Document.Descendants<LeafBlock>())
-        {
-            if (leaf.Inline is not null)
-            {
-                SubstituteInlineTree(leaf.Inline, prefixTree, stack);
-            }
-        }
+        foreach (var leaf in inlineProcessor.Document.Descendants<LeafBlock>())
+        {
+            if (leaf.Inline is null)
+            {
+                continue;
+            }
+
+            // If the leaf's inline is a single LiteralInline, the parser did not create a
+            // ContainerInline for the paragraph. Abbreviation processing expects a container
+            // to be present so that we can insert abbreviation nodes alongside literals.
+            // Wrap the literal in a ContainerInline to match the original behaviour and
+            // the expectations of the tests.
+            if (leaf.Inline is LiteralInline singleLiteral && singleLiteral.Parent is null)
+            {
+                var container = new ContainerInline
+                {
+                    Span = singleLiteral.Span,
+                    Line = singleLiteral.Line,
+                    Column = singleLiteral.Column,
+                };
+                // Move the literal into the new container
+                container.AppendChild(singleLiteral);
+                leaf.Inline = container;
+            }
+
+            SubstituteInlineTree(leaf.Inline, prefixTree, stack);
+        }
*** End of File ***