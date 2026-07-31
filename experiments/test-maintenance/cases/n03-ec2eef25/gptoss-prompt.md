You are maintaining a C#/.NET library. A change was recently applied to this repository.
Review the recent change and the current test results, then decide whether any modification
is needed: update tests, fix production code, or no change at all.

Constraints:
- The first line of your reply must be exactly one of: `DECISION: no_change`, `DECISION: fix_tests`, `DECISION: fix_production`.
- If the decision is `fix_tests` or `fix_production`, follow the DECISION line with a unified diff implementing the fix. If the decision is `no_change`, output no diff.
- Allowed files: src/Markdig/Helpers/HtmlHelper.cs, src/Markdig/Parsers/Inlines/LinkInlineParser.cs.
- Do not weaken, delete, or skip assertions.
- Preserve nearby behavior that is still expected to pass.

Recent change applied to the repository:
<recent_change_diff>
diff --git a/src/Markdig/Helpers/HtmlHelper.cs b/src/Markdig/Helpers/HtmlHelper.cs
index 83f18bcb..4887653f 100644
--- a/src/Markdig/Helpers/HtmlHelper.cs
+++ b/src/Markdig/Helpers/HtmlHelper.cs
@@ -465,24 +465,6 @@ private static bool TryParseHtmlTagProcessingInstruction(ref StringSlice text, r
         }
     }
 
-    /// <summary>
-    /// Destructively unescape a string: remove backslashes before punctuation or symbol characters.
-    /// </summary>
-    /// <param name="text">The string data that will be changed by unescaping any punctuation or symbol characters.</param>
-    /// <param name="removeBackSlash">if set to <c>true</c> [remove back slash].</param>
-    /// <returns>Unescaped text, or null if <paramref name="text"/> is null.<returns>
-    public static string? UnescapeNullable(string? text, bool removeBackSlash = true)
-    {
-        if (text == null)
-        {
-            return null;
-        }
-        else
-        {
-            return Unescape(text, removeBackSlash);
-        }
-    }
-
     /// <summary>
     /// Destructively unescape a string: remove backslashes before punctuation or symbol characters.
     /// </summary>
diff --git a/src/Markdig/Parsers/Inlines/LinkInlineParser.cs b/src/Markdig/Parsers/Inlines/LinkInlineParser.cs
index a982eb37..a9687a31 100644
--- a/src/Markdig/Parsers/Inlines/LinkInlineParser.cs
+++ b/src/Markdig/Parsers/Inlines/LinkInlineParser.cs
@@ -260,7 +260,7 @@ private bool TryProcessLinkOrImage(InlineProcessor inlineState, ref StringSlice
                     link = new LinkInline()
                     {
                         Url = HtmlHelper.Unescape(url, removeBackSlash: false),
-                        Title = HtmlHelper.UnescapeNullable(title, removeBackSlash: false),
+                        Title = title is null ? null : HtmlHelper.Unescape(title, removeBackSlash: false),
                         IsImage = openParent.IsImage,
                         LabelSpan = openParent.LabelSpan,
                         UrlSpan = inlineState.GetSourcePositionFromLocalSpan(linkSpan),
</recent_change_diff>

Current test results:
<test_output>
Test run for <worktree>/src/Markdig.Tests/bin/Release/net9.0/Markdig.Tests.dll (.NETCoreApp,Version=v9.0)
A total of 1 test files matched the specified pattern.
  Skipped ListUnorderedLooseTop [< 1 ms]

Passed!  - Failed:     0, Passed:  3539, Skipped:     1, Total:  3540, Duration: 924 ms - Markdig.Tests.dll (net9.0)
</test_output>

<production_snippet path="src/Markdig/Helpers/HtmlHelper.cs" lines="443-493">
    }

    private static bool TryParseHtmlTagProcessingInstruction(ref StringSlice text, ref ValueStringBuilder builder)
    {
        builder.Append('?');
        var prevChar = '\0';
        while (true)
        {
            var c = text.NextChar();
            if (c == '\0')
            {
                return false;
            }

            if (c == '>' && prevChar == '?')
            {
                builder.Append('>');
                text.SkipChar();
                return true;
            }
            prevChar = c;
            builder.Append(c);
        }
    }

    /// <summary>
    /// Destructively unescape a string: remove backslashes before punctuation or symbol characters.
    /// </summary>
    /// <param name="text">The string data that will be changed by unescaping any punctuation or symbol characters.</param>
    /// <param name="removeBackSlash">if set to <c>true</c> [remove back slash].</param>
    /// <returns></returns>
    public static string Unescape(string? text, bool removeBackSlash = true)
    {
        // Credits: code from CommonMark.NET
        // Copyright (c) 2014, Kārlis Gaņģis All rights reserved. 
        // See license for details:  https://github.com/Knagis/CommonMark.NET/blob/master/LICENSE.md
        if (string.IsNullOrEmpty(text))
        {
            return string.Empty;
        }

        // remove backslashes before punctuation chars:
        int searchPos = 0;
        int lastPos = 0;
        char c = '\0';
        char[] search = removeBackSlash ? SearchBackAndAmp : SearchAmp;
        var sb = new ValueStringBuilder(stackalloc char[ValueStringBuilder.StackallocThreshold]);

        while ((searchPos = text!.IndexOfAny(search, searchPos)) != -1)
        {
            c = text[searchPos];
</production_snippet>

<production_snippet path="src/Markdig/Parsers/Inlines/LinkInlineParser.cs" lines="238-288">

        // If we find one and it’s active,
        // then we parse ahead to see if we have
        // an inline link/image, reference link/image,
        // compact reference link/image,
        // or shortcut reference link/image
        var parentDelimiter = openParent.Parent;
        var savedText = text;

        if (text.CurrentChar == '(')
        {
            LinkInline? link = null;

            if (inlineState.TrackTrivia)
            {
                link = TryParseInlineLinkTrivia(ref text, inlineState, openParent);
            }
            else
            {
                if (LinkHelper.TryParseInlineLink(ref text, out string? url, out string? title, out SourceSpan linkSpan, out SourceSpan titleSpan))
                {
                    // Inline Link
                    link = new LinkInline()
                    {
                        Url = HtmlHelper.Unescape(url, removeBackSlash: false),
                        Title = title is null ? null : HtmlHelper.Unescape(title, removeBackSlash: false),
                        IsImage = openParent.IsImage,
                        LabelSpan = openParent.LabelSpan,
                        UrlSpan = inlineState.GetSourcePositionFromLocalSpan(linkSpan),
                        TitleSpan = inlineState.GetSourcePositionFromLocalSpan(titleSpan),
                        Span = new SourceSpan(openParent.Span.Start, inlineState.GetSourcePosition(text.Start - 1)),
                        Line = openParent.Line,
                        Column = openParent.Column,
                    };
                }
            }

            if (link is not null)
            {
                openParent.ReplaceBy(link);
                // Notifies processor as we are creating an inline locally
                inlineState.Inline = link;

                // Process emphasis delimiters
                inlineState.PostProcessInlines(0, link, null, false);

                // If we have a link (and not an image),
                // we also set all [ delimiters before the opening delimiter to inactive.
                // (This will prevent us from getting links within links.)
                if (!openParent.IsImage)
                {
</production_snippet>
