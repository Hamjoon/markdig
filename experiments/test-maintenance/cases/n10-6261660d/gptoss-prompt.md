You are maintaining a C#/.NET library. A change was recently applied to this repository.
Review the recent change and the current test results, then decide whether any modification
is needed: update tests, fix production code, or no change at all.

Constraints:
- The first line of your reply must be exactly one of: `DECISION: no_change`, `DECISION: fix_tests`, `DECISION: fix_production`.
- If the decision is `fix_tests` or `fix_production`, follow the DECISION line with a unified diff implementing the fix. If the decision is `no_change`, output no diff.
- Allowed files: src/Markdig/Helpers/LinkHelper.cs.
- Do not weaken, delete, or skip assertions.
- Preserve nearby behavior that is still expected to pass.

Recent change applied to the repository:
<recent_change_diff>
diff --git a/src/Markdig/Helpers/LinkHelper.cs b/src/Markdig/Helpers/LinkHelper.cs
index 3a9f9bb6..c5004594 100644
--- a/src/Markdig/Helpers/LinkHelper.cs
+++ b/src/Markdig/Helpers/LinkHelper.cs
@@ -411,7 +411,7 @@ public static bool TryParseInlineLink(ref StringSlice text, out string? link, ou
         {
             // Skip ')'
             text.SkipChar();
-            // not to normalize nulls
+            // not to normalize nulls into empty strings, since LinkInline.Title property is nullable.
         }
 
         return isValid;
@@ -1565,4 +1565,4 @@ public static bool TryParseLabelTrivia<T>(ref T lines, bool allowEmpty, out stri
         label = buffer.ToString();
         return true;
     }
-}
\ No newline at end of file
+}
</recent_change_diff>

Current test results:
<test_output>
Test run for <worktree>/src/Markdig.Tests/bin/Release/net9.0/Markdig.Tests.dll (.NETCoreApp,Version=v9.0)
A total of 1 test files matched the specified pattern.
  Skipped ListUnorderedLooseTop [< 1 ms]

Passed!  - Failed:     0, Passed:  3539, Skipped:     1, Total:  3540, Duration: 923 ms - Markdig.Tests.dll (net9.0)
</test_output>

<production_snippet path="src/Markdig/Helpers/LinkHelper.cs" lines="389-439">
                    }
                    else if (TryParseTitle(ref text, out title, out char enclosingCharacter))
                    {
                        titleSpan.Start = pos;
                        titleSpan.End = text.Start - 1;
                        if (titleSpan.End < titleSpan.Start)
                        {
                            titleSpan = SourceSpan.Empty;
                        }
                        text.TrimStart();
                        c = text.CurrentChar;

                        if (c == ')')
                        {
                            isValid = true;
                        }
                    }
                }
            }
        }

        if (isValid)
        {
            // Skip ')'
            text.SkipChar();
            // not to normalize nulls into empty strings, since LinkInline.Title property is nullable.
        }

        return isValid;
    }

    public static bool TryParseInlineLinkTrivia(
        ref StringSlice text,
        [NotNullWhen(true)] out string? link,
        out SourceSpan unescapedLink,
        out string? title,
        out SourceSpan unescapedTitle,
        out char titleEnclosingCharacter,
        out SourceSpan linkSpan,
        out SourceSpan titleSpan,
        out SourceSpan triviaBeforeLink,
        out SourceSpan triviaAfterLink,
        out SourceSpan triviaAfterTitle,
        out bool urlHasPointyBrackets)
    {
        // 1. An inline link consists of a link text followed immediately by a left parenthesis (, 
        // 2. optional whitespace,  TODO: specs: is it whitespace or multiple whitespaces?
        // 3. an optional link destination, 
        // 4. an optional link title separated from the link destination by whitespace, 
        // 5. optional whitespace,  TODO: specs: is it whitespace or multiple whitespaces?
        // 6. and a right parenthesis )
</production_snippet>

<production_snippet path="src/Markdig/Helpers/LinkHelper.cs" lines="1543-1568">
                    if (isWhitespace)
                    {
                        // Replace any whitespace by a single ' '
                        buffer.Append(' ');
                    }
                    else
                    {
                        buffer.Append(c);
                    }
                    if (!isWhitespace)
                    {
                        hasNonWhiteSpace = true;
                    }
                }
            }
            previousWhitespace = isWhitespace;
        }

        buffer.Dispose();
        return false;

    ReturnValid:
        label = buffer.ToString();
        return true;
    }
}
</production_snippet>
