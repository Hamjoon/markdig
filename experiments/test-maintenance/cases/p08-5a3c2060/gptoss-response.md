DECISION: fix_production
diff --git a/src/Markdig/Renderers/Roundtrip/ListRenderer.cs b/src/Markdig/Renderers/Roundtrip/ListRenderer.cs
index 1c2d3e4..5f6a7b8 100644
--- a/src/Markdig/Renderers/Roundtrip/ListRenderer.cs
+++ b/src/Markdig/Renderers/Roundtrip/ListRenderer.cs
@@
                 StringSlice bws = listItem.TriviaBefore;
                 char bullet = listBlock.BulletType;
                 StringSlice aws = listItem.TriviaAfter;
 
                 renderer.PushIndent(new string[] { $"{bws}{bullet}{aws}" });
-                if (listItem.Count == 0)
-                {
-                    renderer.Write(""); // trigger writing of indent
-                }
-                else
-                {
-                    renderer.WriteChildren(listItem);
-                }
+                if (listItem.Count == 0)
+                {
+                    // When there are no child blocks (e.g., a list item that only contains plain text
+                    // without a paragraph block), the parser may not have created any children.
+                    // In such cases we need to render the raw line content that follows the bullet.
+                    // The raw line is stored in listItem.Lines. We extract the part of the line that
+                    // comes after the leading whitespace, bullet character and any whitespace that
+                    // follows the bullet (aws).
+                    if (listItem.Lines.Count > 0)
+                    {
+                        var line = listItem.Lines[0];
+                        // Compute the start position after bws, bullet and aws
+                        int start = line.Start + bws.Length + 1 + aws.Length;
+                        int length = line.End - start + 1;
+                        if (length > 0)
+                        {
+                            // Write the remaining text of the line
+                            renderer.Write(line.Text.Substring(start, length));
+                        }
+                    }
+                    // Ensure the indent (including bullet and any trailing whitespace) is written
+                    renderer.Write(""); // trigger writing of indent
+                }
+                else
+                {
+                    renderer.WriteChildren(listItem);
+                }
                 renderer.PopIndent();
             }
         }
     }