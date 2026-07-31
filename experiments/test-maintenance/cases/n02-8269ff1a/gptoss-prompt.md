You are maintaining a C#/.NET library. A change was recently applied to this repository.
Review the recent change and the current test results, then decide whether any modification
is needed: update tests, fix production code, or no change at all.

Constraints:
- The first line of your reply must be exactly one of: `DECISION: no_change`, `DECISION: fix_tests`, `DECISION: fix_production`.
- If the decision is `fix_tests` or `fix_production`, follow the DECISION line with a unified diff implementing the fix. If the decision is `no_change`, output no diff.
- Allowed files: src/Markdig/Extensions/AutoLinks/AutoLinkParser.cs, src/Markdig/Helpers/StringSlice.cs, src/Markdig/Polyfills/SpanExtensions.cs.
- Do not weaken, delete, or skip assertions.
- Preserve nearby behavior that is still expected to pass.

Recent change applied to the repository:
<recent_change_diff>
diff --git a/src/Markdig/Extensions/AutoLinks/AutoLinkParser.cs b/src/Markdig/Extensions/AutoLinks/AutoLinkParser.cs
index 6ee6b9f0..0b0fba26 100644
--- a/src/Markdig/Extensions/AutoLinks/AutoLinkParser.cs
+++ b/src/Markdig/Extensions/AutoLinks/AutoLinkParser.cs
@@ -6,6 +6,8 @@
 using Markdig.Parsers;
 using Markdig.Renderers.Html;
 using Markdig.Syntax.Inlines;
+using System.Buffers;
+using System.Diagnostics;
 
 namespace Markdig.Extensions.AutoLinks;
 
@@ -31,186 +33,171 @@ public AutoLinkParser(AutoLinkOptions options)
             'w', // for www.
         ];
 
-        _listOfCharCache = new ListOfCharCache();
+        _validPreviousCharacters = SearchValues.Create(options.ValidPreviousCharacters);
     }
 
     public readonly AutoLinkOptions Options;
 
-    private readonly ListOfCharCache _listOfCharCache;
+    private readonly SearchValues<char> _validPreviousCharacters;
 
+    // This is a particularly expensive parser as it gets called for many common letters.
     public override bool Match(InlineProcessor processor, ref StringSlice slice)
     {
         // Previous char must be a whitespace or a punctuation
         var previousChar = slice.PeekCharExtra(-1);
-        if (!previousChar.IsWhiteSpaceOrZero() && Options.ValidPreviousCharacters.IndexOf(previousChar) == -1)
+        if (!previousChar.IsWhiteSpaceOrZero() && !_validPreviousCharacters.Contains(previousChar))
         {
             return false;
         }
 
-        var startPosition = slice.Start;
-        int domainOffset = 0;
+        ReadOnlySpan<char> span = slice.AsSpan();
+
+        Debug.Assert(span[0] is 'h' or 'f' or 'm' or 't' or 'w');
 
-        var c = slice.CurrentChar;
         // Precheck URL
-        switch (c)
+        bool mayBeValid = span.Length >= 4 && span[0] switch
         {
-            case 'h':
-                if (slice.MatchLowercase("ttp://", 1))
+            'h' => span.StartsWith("https://", StringComparison.Ordinal) || span.StartsWith("http://", StringComparison.Ordinal),
+            'w' => span.StartsWith("www.", StringComparison.Ordinal), // We won't match http:/www. or /www.xxx
+            'f' => span.StartsWith("ftp://", StringComparison.Ordinal),
+            'm' => span.StartsWith("mailto:", StringComparison.Ordinal),
+            _ => span.StartsWith("tel:", StringComparison.Ordinal),
+        };
+
+        return mayBeValid && MatchCore(processor, ref slice);
+    }
+
+    private bool MatchCore(InlineProcessor processor, ref StringSlice slice)
+    {
+        char c = slice.CurrentChar;
+        var startPosition = slice.Start;
+
+        // We don't bother disposing the builder as it'll realistically never grow beyond the initial stack size.
+        var pendingEmphasis = new ValueStringBuilder(stackalloc char[32]);
+
+        // Check that an autolink is possible in the current context
+        if (!IsAutoLinkValidInCurrentContext(processor, ref pendingEmphasis))
+        {
+            return false;
+        }
+
+        // Parse URL
+        if (!LinkHelper.TryParseUrl(ref slice, out string? link, out _, true))
+        {
+            return false;
+        }
+
+        // If we have any pending emphasis, remove any pending emphasis characters from the end of the link
+        if (pendingEmphasis.Length > 0)
+        {
+            for (int i = link.Length - 1; i >= 0; i--)
+            {
+                if (pendingEmphasis.AsSpan().Contains(link[i]))
                 {
-                    domainOffset = 7; // http://
+                    slice.Start--;
                 }
-                else if (slice.MatchLowercase("ttps://", 1))
+                else
                 {
-                    domainOffset = 8; // https://
+                    if (i < link.Length - 1)
+                    {
+                        link = link.Substring(0, i + 1);
+                    }
+                    break;
                 }
-                else return false;
-                break;
-            case 'f':
-                if (!slice.MatchLowercase("tp://", 1))
+            }
+        }
+
+        int domainOffset = 0;
+
+        // Post-check URL
+        switch (c)
+        {
+            case 'h':
+                if (string.Equals(link, "http://", StringComparison.Ordinal) ||
+                    string.Equals(link, "https://", StringComparison.Ordinal))
                 {
                     return false;
                 }
-                domainOffset = 6; // ftp://
+                domainOffset = link[4] == 's' ? 8 : 7; // https:// or http://
                 break;
-            case 'm':
-                if (!slice.MatchLowercase("ailto:", 1))
+
+            case 'w':
+                domainOffset = 4; // www.
+                break;
+
+            case 'f':
+                if (string.Equals(link, "ftp://", StringComparison.Ordinal))
                 {
                     return false;
                 }
+                domainOffset = 6; // ftp://
                 break;
+
             case 't':
-                if (!slice.MatchLowercase("el:", 1))
+                if (string.Equals(link, "tel", StringComparison.Ordinal))
                 {
                     return false;
                 }
-                domainOffset = 4;
                 break;
-            case 'w':
-                if (!slice.MatchLowercase("ww.", 1)) // We won't match http:/www. or /www.xxx
+
+            case 'm':
+                int atIndex = link.IndexOf('@');
+                if (atIndex == -1 ||
+                    atIndex == 7) // mailto:@ - no email part
                 {
                     return false;
                 }
-                domainOffset = 4; // www.
+                domainOffset = atIndex + 1;
                 break;
         }
 
-        List<char> pendingEmphasis = _listOfCharCache.Get();
-        try
+        // Do not need to check if a telephone number is a valid domain
+        if (c != 't' && !LinkHelper.IsValidDomain(link, domainOffset, Options.AllowDomainWithoutPeriod))
         {
-            // Check that an autolink is possible in the current context
-            if (!IsAutoLinkValidInCurrentContext(processor, pendingEmphasis))
-            {
-                return false;
-            }
-
-            // Parse URL
-            if (!LinkHelper.TryParseUrl(ref slice, out string? link, out _, true))
-            {
-                return false;
-            }
-
-
-            // If we have any pending emphasis, remove any pending emphasis characters from the end of the link
-            if (pendingEmphasis.Count > 0)
-            {
-                for (int i = link.Length - 1; i >= 0; i--)
-                {
-                    if (pendingEmphasis.Contains(link[i]))
-                    {
-                        slice.Start--;
-                    }
-                    else
-                    {
-                        if (i < link.Length - 1)
-                        {
-                            link = link.Substring(0, i + 1);
-                        }
-                        break;
-                    }
-                }
-            }
+            return false;
+        }
 
-            // Post-check URL
-            switch (c)
+        var inline = new LinkInline()
+        {
+            Span =
             {
-                case 'h':
-                    if (string.Equals(link, "http://", StringComparison.OrdinalIgnoreCase) ||
-                        string.Equals(link, "https://", StringComparison.OrdinalIgnoreCase))
-                    {
-                        return false;
-                    }
-                    break;
-                case 'f':
-                    if (string.Equals(link, "ftp://", StringComparison.OrdinalIgnoreCase))
-                    {
-                        return false;
-                    }
-                    break;
-                case 't':
-                    if (string.Equals(link, "tel", StringComparison.OrdinalIgnoreCase))
-                    {
-                        return false;
-                    }
-                    break;
-                case 'm':
-                    int atIndex = link.IndexOf('@');
-                    if (atIndex == -1 ||
-                        atIndex == 7) // mailto:@ - no email part
-                    {
-                        return false;
-                    }
-                    domainOffset = atIndex + 1;
-                    break;
-            }
+                Start = processor.GetSourcePosition(startPosition, out int line, out int column),
+            },
+            Line = line,
+            Column = column,
+            Url = c == 'w' ? ((Options.UseHttpsForWWWLinks ? "https://" : "http://") + link) : link,
+            IsClosed = true,
+            IsAutoLink = true,
+        };
 
-            // Do not need to check if a telephone number is a valid domain
-            if (c != 't' && !LinkHelper.IsValidDomain(link, domainOffset, Options.AllowDomainWithoutPeriod))
-            {
-                return false;
-            }
+        int skipFromBeginning = c switch
+        {
+            'm' => 7, // For mailto: skip "mailto:" for content
+            't' => 4, // Same but for tel:
+            _ => 0
+        };
 
-            var inline = new LinkInline()
-            {
-                Span =
-                {
-                    Start = processor.GetSourcePosition(startPosition, out int line, out int column),
-                },
-                Line = line,
-                Column = column,
-                Url = c == 'w' ? ((Options.UseHttpsForWWWLinks ? "https://" : "http://") + link) : link,
-                IsClosed = true,
-                IsAutoLink = true,
-            };
-
-            var skipFromBeginning = c == 'm' ? 7 : 0; // For mailto: skip "mailto:" for content
-            skipFromBeginning = c == 't' ? 4 : skipFromBeginning; // See above but for tel:
-
-            inline.Span.End = inline.Span.Start + link.Length - 1;
-            inline.UrlSpan = inline.Span;
-            inline.AppendChild(new LiteralInline()
-            {
-                Span = inline.Span,
-                Line = line,
-                Column = column,
-                Content = new StringSlice(slice.Text, startPosition + skipFromBeginning, startPosition + link.Length - 1),
-                IsClosed = true
-            });
-            processor.Inline = inline;
-
-            if (Options.OpenInNewWindow)
-            {
-                inline.GetAttributes().AddPropertyIfNotExist("target", "_blank");
-            }
+        inline.Span.End = inline.Span.Start + link.Length - 1;
+        inline.UrlSpan = inline.Span;
+        inline.AppendChild(new LiteralInline()
+        {
+            Span = inline.Span,
+            Line = line,
+            Column = column,
+            Content = new StringSlice(slice.Text, startPosition + skipFromBeginning, startPosition + link.Length - 1),
+            IsClosed = true
+        });
+        processor.Inline = inline;
 
-            return true;
-        }
-        finally
+        if (Options.OpenInNewWindow)
         {
-            _listOfCharCache.Release(pendingEmphasis);
+            inline.GetAttributes().AddPropertyIfNotExist("target", "_blank");
         }
+
+        return true;
     }
 
-    private bool IsAutoLinkValidInCurrentContext(InlineProcessor processor, List<char> pendingEmphasis)
+    private static bool IsAutoLinkValidInCurrentContext(InlineProcessor processor, ref ValueStringBuilder pendingEmphasis)
     {
         // Case where there is a pending HtmlInline <a>
         var currentInline = processor.Inline;
@@ -257,9 +244,9 @@ private bool IsAutoLinkValidInCurrentContext(InlineProcessor processor, List<cha
                 // Record all pending characters for emphasis
                 if (currentInline is EmphasisDelimiterInline emphasisDelimiter)
                 {
-                    if (!pendingEmphasis.Contains(emphasisDelimiter.DelimiterChar))
+                    if (!pendingEmphasis.AsSpan().Contains(emphasisDelimiter.DelimiterChar))
                     {
-                        pendingEmphasis.Add(emphasisDelimiter.DelimiterChar);
+                        pendingEmphasis.Append(emphasisDelimiter.DelimiterChar);
                     }
                 }
             }
@@ -268,12 +255,4 @@ private bool IsAutoLinkValidInCurrentContext(InlineProcessor processor, List<cha
 
         return countBrackets <= 0;
     }
-
-    private sealed class ListOfCharCache : DefaultObjectCache<List<char>>
-    {
-        protected override void Reset(List<char> instance)
-        {
-            instance.Clear();
-        }
-    }
 }
\ No newline at end of file
diff --git a/src/Markdig/Helpers/StringSlice.cs b/src/Markdig/Helpers/StringSlice.cs
index 95ddad99..ed1bea66 100644
--- a/src/Markdig/Helpers/StringSlice.cs
+++ b/src/Markdig/Helpers/StringSlice.cs
@@ -231,7 +231,7 @@ public readonly char PeekCharAbsolute(int index)
     }
 
     /// <summary>
-    /// Peeks a character at the specified offset from the current begining of the slice
+    /// Peeks a character at the specified offset from the current beginning of the slice
     /// without using the range <see cref="Start"/> or <see cref="End"/>, returns `\0` if outside the <see cref="Text"/>.
     /// </summary>
     /// <param name="offset">The offset.</param>
diff --git a/src/Markdig/Polyfills/SpanExtensions.cs b/src/Markdig/Polyfills/SpanExtensions.cs
new file mode 100644
index 00000000..caf61cac
--- /dev/null
+++ b/src/Markdig/Polyfills/SpanExtensions.cs
@@ -0,0 +1,23 @@
+// Copyright (c) Alexandre Mutel. All rights reserved.
+// This file is licensed under the BSD-Clause 2 license.
+// See the license.txt file in the project root for more information.
+
+#if NET462 || NETSTANDARD2_0
+
+using System.Diagnostics;
+
+namespace System;
+
+internal static class SpanExtensions
+{
+    public static bool StartsWith(this ReadOnlySpan<char> span, string prefix, StringComparison comparisonType)
+    {
+        Debug.Assert(comparisonType is StringComparison.Ordinal or StringComparison.OrdinalIgnoreCase);
+
+        return
+            span.Length >= prefix.Length &&
+            span.Slice(0, prefix.Length).Equals(prefix.AsSpan(), comparisonType);
+    }
+}
+
+#endif
\ No newline at end of file
</recent_change_diff>

Current test results:
<test_output>
Test run for <worktree>/src/Markdig.Tests/bin/Release/net9.0/Markdig.Tests.dll (.NETCoreApp,Version=v9.0)
A total of 1 test files matched the specified pattern.
  Skipped ListUnorderedLooseTop [< 1 ms]

Passed!  - Failed:     0, Passed:  3468, Skipped:     1, Total:  3469, Duration: 2 s - Markdig.Tests.dll (net9.0)
</test_output>

<production_snippet path="src/Markdig/Extensions/AutoLinks/AutoLinkParser.cs" lines="1-220">
// Copyright (c) Alexandre Mutel. All rights reserved.
// This file is licensed under the BSD-Clause 2 license. 
// See the license.txt file in the project root for more information.

using Markdig.Helpers;
using Markdig.Parsers;
using Markdig.Renderers.Html;
using Markdig.Syntax.Inlines;
using System.Buffers;
using System.Diagnostics;

namespace Markdig.Extensions.AutoLinks;

/// <summary>
/// The inline parser used to for autolinks.
/// </summary>
/// <seealso cref="InlineParser" />
public class AutoLinkParser : InlineParser
{
    /// <summary>
    /// Initializes a new instance of the <see cref="AutoLinkParser"/> class.
    /// </summary>
    public AutoLinkParser(AutoLinkOptions options)
    {
        Options = options ?? throw new ArgumentNullException(nameof(options));

        OpeningCharacters =
        [
            'h', // for http:// and https://
            'f', // for ftp://
            'm', // for mailto:
            't', // for tel:
            'w', // for www.
        ];

        _validPreviousCharacters = SearchValues.Create(options.ValidPreviousCharacters);
    }

    public readonly AutoLinkOptions Options;

    private readonly SearchValues<char> _validPreviousCharacters;

    // This is a particularly expensive parser as it gets called for many common letters.
    public override bool Match(InlineProcessor processor, ref StringSlice slice)
    {
        // Previous char must be a whitespace or a punctuation
        var previousChar = slice.PeekCharExtra(-1);
        if (!previousChar.IsWhiteSpaceOrZero() && !_validPreviousCharacters.Contains(previousChar))
        {
            return false;
        }

        ReadOnlySpan<char> span = slice.AsSpan();

        Debug.Assert(span[0] is 'h' or 'f' or 'm' or 't' or 'w');

        // Precheck URL
        bool mayBeValid = span.Length >= 4 && span[0] switch
        {
            'h' => span.StartsWith("https://", StringComparison.Ordinal) || span.StartsWith("http://", StringComparison.Ordinal),
            'w' => span.StartsWith("www.", StringComparison.Ordinal), // We won't match http:/www. or /www.xxx
            'f' => span.StartsWith("ftp://", StringComparison.Ordinal),
            'm' => span.StartsWith("mailto:", StringComparison.Ordinal),
            _ => span.StartsWith("tel:", StringComparison.Ordinal),
        };

        return mayBeValid && MatchCore(processor, ref slice);
    }

    private bool MatchCore(InlineProcessor processor, ref StringSlice slice)
    {
        char c = slice.CurrentChar;
        var startPosition = slice.Start;

        // We don't bother disposing the builder as it'll realistically never grow beyond the initial stack size.
        var pendingEmphasis = new ValueStringBuilder(stackalloc char[32]);

        // Check that an autolink is possible in the current context
        if (!IsAutoLinkValidInCurrentContext(processor, ref pendingEmphasis))
        {
            return false;
        }

        // Parse URL
        if (!LinkHelper.TryParseUrl(ref slice, out string? link, out _, true))
        {
            return false;
        }

        // If we have any pending emphasis, remove any pending emphasis characters from the end of the link
        if (pendingEmphasis.Length > 0)
        {
            for (int i = link.Length - 1; i >= 0; i--)
            {
                if (pendingEmphasis.AsSpan().Contains(link[i]))
                {
                    slice.Start--;
                }
                else
                {
                    if (i < link.Length - 1)
                    {
                        link = link.Substring(0, i + 1);
                    }
                    break;
                }
            }
        }

        int domainOffset = 0;

        // Post-check URL
        switch (c)
        {
            case 'h':
                if (string.Equals(link, "http://", StringComparison.Ordinal) ||
                    string.Equals(link, "https://", StringComparison.Ordinal))
                {
                    return false;
                }
                domainOffset = link[4] == 's' ? 8 : 7; // https:// or http://
                break;

            case 'w':
                domainOffset = 4; // www.
                break;

            case 'f':
                if (string.Equals(link, "ftp://", StringComparison.Ordinal))
                {
                    return false;
                }
                domainOffset = 6; // ftp://
                break;

            case 't':
                if (string.Equals(link, "tel", StringComparison.Ordinal))
                {
                    return false;
                }
                break;

            case 'm':
                int atIndex = link.IndexOf('@');
                if (atIndex == -1 ||
                    atIndex == 7) // mailto:@ - no email part
                {
                    return false;
                }
                domainOffset = atIndex + 1;
                break;
        }

        // Do not need to check if a telephone number is a valid domain
        if (c != 't' && !LinkHelper.IsValidDomain(link, domainOffset, Options.AllowDomainWithoutPeriod))
        {
            return false;
        }

        var inline = new LinkInline()
        {
            Span =
            {
                Start = processor.GetSourcePosition(startPosition, out int line, out int column),
            },
            Line = line,
            Column = column,
            Url = c == 'w' ? ((Options.UseHttpsForWWWLinks ? "https://" : "http://") + link) : link,
            IsClosed = true,
            IsAutoLink = true,
        };

        int skipFromBeginning = c switch
        {
            'm' => 7, // For mailto: skip "mailto:" for content
            't' => 4, // Same but for tel:
            _ => 0
        };

        inline.Span.End = inline.Span.Start + link.Length - 1;
        inline.UrlSpan = inline.Span;
        inline.AppendChild(new LiteralInline()
        {
            Span = inline.Span,
            Line = line,
            Column = column,
            Content = new StringSlice(slice.Text, startPosition + skipFromBeginning, startPosition + link.Length - 1),
            IsClosed = true
        });
        processor.Inline = inline;

        if (Options.OpenInNewWindow)
        {
            inline.GetAttributes().AddPropertyIfNotExist("target", "_blank");
        }

        return true;
    }

    private static bool IsAutoLinkValidInCurrentContext(InlineProcessor processor, ref ValueStringBuilder pendingEmphasis)
    {
        // Case where there is a pending HtmlInline <a>
        var currentInline = processor.Inline;
        while (currentInline != null)
        {
            if (currentInline is HtmlInline htmlInline)
            {
                // If we have a </a> we don't expect nested <a>
                if (htmlInline.Tag.StartsWith("</a", StringComparison.OrdinalIgnoreCase))
                {
                    break;
                }

                // If there is a pending <a>, we can't allow a link
                if (htmlInline.Tag.StartsWith("<a", StringComparison.OrdinalIgnoreCase))
                {
                    return false;
                }
            }

</production_snippet>

<production_snippet path="src/Markdig/Helpers/StringSlice.cs" lines="209-259">
    /// <summary>
    /// Peeks a character at the specified offset from the current <see cref="Start"/> position
    /// inside the range <see cref="Start"/> and <see cref="End"/>, returns `\0` if outside this range.
    /// </summary>
    /// <param name="offset">The offset.</param>
    /// <returns>The character at offset, returns `\0` if none.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public readonly char PeekChar(int offset)
    {
        var index = Start + offset;
        return index >= Start && index <= End ? Text[index] : '\0';
    }

    /// <summary>
    /// Peeks a character at the specified offset from the current beginning of the string, without taking into account <see cref="Start"/> and <see cref="End"/>
    /// </summary>
    /// <returns>The character at offset, returns `\0` if none.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public readonly char PeekCharAbsolute(int index)
    {
        string text = Text;
        return (uint)index < (uint)text.Length ? text[index] : '\0';
    }

    /// <summary>
    /// Peeks a character at the specified offset from the current beginning of the slice
    /// without using the range <see cref="Start"/> or <see cref="End"/>, returns `\0` if outside the <see cref="Text"/>.
    /// </summary>
    /// <param name="offset">The offset.</param>
    /// <returns>The character at offset, returns `\0` if none.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public readonly char PeekCharExtra(int offset)
    {
        var index = Start + offset;
        var text = Text;
        return (uint)index < (uint)text.Length ? text[index] : '\0';
    }

    /// <summary>
    /// Matches the specified text.
    /// </summary>
    /// <param name="text">The text.</param>
    /// <param name="offset">The offset.</param>
    /// <returns><c>true</c> if the text matches; <c>false</c> otherwise</returns>
    public readonly bool Match(string text, int offset = 0)
    {
        return Match(text, End, offset);
    }

    /// <summary>
    /// Matches the specified text.
</production_snippet>

<production_snippet path="src/Markdig/Polyfills/SpanExtensions.cs" lines="1-23">
// Copyright (c) Alexandre Mutel. All rights reserved.
// This file is licensed under the BSD-Clause 2 license.
// See the license.txt file in the project root for more information.

#if NET462 || NETSTANDARD2_0

using System.Diagnostics;

namespace System;

internal static class SpanExtensions
{
    public static bool StartsWith(this ReadOnlySpan<char> span, string prefix, StringComparison comparisonType)
    {
        Debug.Assert(comparisonType is StringComparison.Ordinal or StringComparison.OrdinalIgnoreCase);

        return
            span.Length >= prefix.Length &&
            span.Slice(0, prefix.Length).Equals(prefix.AsSpan(), comparisonType);
    }
}

#endif
</production_snippet>
