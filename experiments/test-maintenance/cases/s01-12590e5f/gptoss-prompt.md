You are maintaining a C#/.NET library. A change was recently applied to this repository.
Review the recent change and the current test results, then decide whether any modification
is needed: update tests, fix production code, or no change at all.

Constraints:
- The first line of your reply must be exactly one of: `DECISION: no_change`, `DECISION: fix_tests`, `DECISION: fix_production`.
- If the decision is `fix_tests` or `fix_production`, follow the DECISION line with a unified diff implementing the fix. If the decision is `no_change`, output no diff.
- Allowed files: src/Markdig.Tests/TestLinkHelper.cs, src/Markdig/Helpers/LinkHelper.cs.
- Do not weaken, delete, or skip assertions.
- Preserve nearby behavior that is still expected to pass.

Recent change applied to the repository:
<recent_change_diff>
diff --git a/src/Markdig/Helpers/LinkHelper.cs b/src/Markdig/Helpers/LinkHelper.cs
index c5004594..fd7e6ba2 100644
--- a/src/Markdig/Helpers/LinkHelper.cs
+++ b/src/Markdig/Helpers/LinkHelper.cs
@@ -2,11 +2,13 @@
 // This file is licensed under the BSD-Clause 2 license. 
 // See the license.txt file in the project root for more information.
 
+using Markdig.Syntax;
 using System.Buffers;
 using System.Diagnostics;
 using System.Diagnostics.CodeAnalysis;
+using System.Globalization;
 using System.Runtime.CompilerServices;
-using Markdig.Syntax;
+using System.Text;
 
 namespace Markdig.Helpers;
 
@@ -30,11 +32,38 @@ public static string Urilize(ReadOnlySpan<char> headingText, bool allowOnlyAscii
         var headingBuffer = new ValueStringBuilder(stackalloc char[ValueStringBuilder.StackallocThreshold]);
         bool hasLetter = keepOpeningDigits && headingText.Length > 0 && char.IsLetterOrDigit(headingText[0]);
         bool previousIsSpace = false;
-        for (int i = 0; i < headingText.Length; i++)
+
+        // First normalize the string to decompose characters if allowOnlyAscii is true
+        string normalizedString = string.Empty;
+        if (allowOnlyAscii)
         {
-            var c = headingText[i];
-            var normalized = allowOnlyAscii ? CharNormalizer.ConvertToAscii(c) : null;
-            for (int j = 0; j < (normalized?.Length ?? 1); j++)
+            normalizedString = headingText.ToString().Normalize(NormalizationForm.FormD);
+        }
+
+        var textToProcess = string.IsNullOrEmpty(normalizedString) ? headingText : normalizedString.AsSpan();
+
+        for (int i = 0; i < textToProcess.Length; i++)
+        {
+            var c = textToProcess[i];
+
+            // Skip combining diacritical marks when normalized
+            if (allowOnlyAscii && CharUnicodeInfo.GetUnicodeCategory(c) == UnicodeCategory.NonSpacingMark)
+            {
+                continue;
+            }
+
+            // Handle German umlauts and Norwegian/Danish characters explicitly (they don't decompose properly)
+            ReadOnlySpan<char> normalized;
+            if (IsSpecialScandinavianOrGermanChar(c))
+            {
+                normalized = NormalizeScandinavianOrGermanChar(c);
+            }
+            else
+            {
+                normalized = allowOnlyAscii ? CharNormalizer.ConvertToAscii(c) : null;
+            }
+
+            for (int j = 0; j < (normalized.Length < 1 ? 1 : normalized.Length); j++)
             {
                 if (normalized != null)
                 {
@@ -101,6 +130,50 @@ public static string Urilize(ReadOnlySpan<char> headingText, bool allowOnlyAscii
         return headingBuffer.ToString();
     }
 
+    [MethodImpl(MethodImplOptions.AggressiveInlining)]
+    private static bool IsSpecialScandinavianOrGermanChar(char c)
+    {
+        // German umlauts and ß
+        // Norwegian/Danish/Swedish æ, ø, å
+        // Icelandic þ (thorn), ð (eth)
+        return c == 'ä' || c == 'ö' || c == 'ü' ||
+               c == 'Ä' || c == 'Ö' || c == 'Ü' ||
+               c == 'ß' ||
+               c == 'æ' || c == 'ø' || c == 'å' ||
+               c == 'Æ' || c == 'Ø' || c == 'Å' ||
+               c == 'þ' || c == 'ð' ||
+               c == 'Þ' || c == 'Ð';
+    }
+
+    [MethodImpl(MethodImplOptions.AggressiveInlining)]
+    private static ReadOnlySpan<char> NormalizeScandinavianOrGermanChar(char c)
+    {
+        return c switch
+        {
+            // German
+            'ä' => "ae",
+            'ö' => "oe",
+            'ü' => "ue",
+            'Ä' => "Ae",
+            'Ö' => "Oe",
+            'Ü' => "Ue",
+            'ß' => "ss",
+            // Norwegian/Danish/Swedish
+            'æ' => "ae",
+            'ø' => "oe",
+            'å' => "aa",
+            'Æ' => "Ae",
+            'Ø' => "Oe",
+            'Å' => "Aa",
+            // Icelandic
+            'þ' => "th",
+            'Þ' => "Th",
+            'ð' => "d",
+            'Ð' => "D",
+            _ => ReadOnlySpan<char>.Empty
+        };
+    }
+
     public static string UrilizeAsGfm(string headingText)
     {
         return UrilizeAsGfm(headingText.AsSpan());
@@ -218,7 +291,8 @@ public static bool TryParseAutolink(ref StringSlice text, [NotNullWhen(true)] ou
                 }
                 state = 1;
                 break;
-            } else if (c == '@')
+            }
+            else if (c == '@')
             {
                 if (state > 0)
                 {
@@ -234,7 +308,7 @@ public static bool TryParseAutolink(ref StringSlice text, [NotNullWhen(true)] ou
         }
 
         // append ':' or '@' 
-        builder.Append(c); 
+        builder.Append(c);
 
         if (state < 0)
         {
</recent_change_diff>

Current test results:
<test_output>
[... truncated, last 120 lines ...]
  Expected: "bær"
  But was:  "baer"
  ------------^

  Stack Trace:
     at NUnit.Framework.Legacy.ClassicAssert.AreEqual(Object expected, Object actual)
   at Markdig.Tests.TestLinkHelper.TestUrilizeNonAscii_Simple(String input, String expectedResult) in <worktree>/src/Markdig.Tests/TestLinkHelper.cs:line 370

1)    at NUnit.Framework.Legacy.ClassicAssert.AreEqual(Object expected, Object actual)
   at Markdig.Tests.TestLinkHelper.TestUrilizeNonAscii_Simple(String input, String expectedResult) in <worktree>/src/Markdig.Tests/TestLinkHelper.cs:line 370


  Failed TestUrilizeNonAscii_Simple("æ5el","æ5el") [< 1 ms]
  Error Message:
     Assert.That(actual, Is.EqualTo(expected))
  Expected string length 4 but was 5. Strings differ at index 0.
  Expected: "æ5el"
  But was:  "ae5el"
  -----------^

  Stack Trace:
     at NUnit.Framework.Legacy.ClassicAssert.AreEqual(Object expected, Object actual)
   at Markdig.Tests.TestLinkHelper.TestUrilizeNonAscii_Simple(String input, String expectedResult) in <worktree>/src/Markdig.Tests/TestLinkHelper.cs:line 370
   at InvokeStub_TestLinkHelper.TestUrilizeNonAscii_Simple(Object, Span`1)

1)    at NUnit.Framework.Legacy.ClassicAssert.AreEqual(Object expected, Object actual)
   at Markdig.Tests.TestLinkHelper.TestUrilizeNonAscii_Simple(String input, String expectedResult) in <worktree>/src/Markdig.Tests/TestLinkHelper.cs:line 370
   at InvokeStub_TestLinkHelper.TestUrilizeNonAscii_Simple(Object, Span`1)


  Failed TestUrilizeNonAscii_Simple("-æ5el","æ5el") [< 1 ms]
  Error Message:
     Assert.That(actual, Is.EqualTo(expected))
  Expected string length 4 but was 5. Strings differ at index 0.
  Expected: "æ5el"
  But was:  "ae5el"
  -----------^

  Stack Trace:
     at NUnit.Framework.Legacy.ClassicAssert.AreEqual(Object expected, Object actual)
   at Markdig.Tests.TestLinkHelper.TestUrilizeNonAscii_Simple(String input, String expectedResult) in <worktree>/src/Markdig.Tests/TestLinkHelper.cs:line 370
   at InvokeStub_TestLinkHelper.TestUrilizeNonAscii_Simple(Object, Span`1)

1)    at NUnit.Framework.Legacy.ClassicAssert.AreEqual(Object expected, Object actual)
   at Markdig.Tests.TestLinkHelper.TestUrilizeNonAscii_Simple(String input, String expectedResult) in <worktree>/src/Markdig.Tests/TestLinkHelper.cs:line 370
   at InvokeStub_TestLinkHelper.TestUrilizeNonAscii_Simple(Object, Span`1)


  Failed TestUrilizeNonAscii_Simple("-frø-","frø") [< 1 ms]
  Error Message:
     Assert.That(actual, Is.EqualTo(expected))
  Expected string length 3 but was 4. Strings differ at index 2.
  Expected: "frø"
  But was:  "froe"
  -------------^

  Stack Trace:
     at NUnit.Framework.Legacy.ClassicAssert.AreEqual(Object expected, Object actual)
   at Markdig.Tests.TestLinkHelper.TestUrilizeNonAscii_Simple(String input, String expectedResult) in <worktree>/src/Markdig.Tests/TestLinkHelper.cs:line 370
   at InvokeStub_TestLinkHelper.TestUrilizeNonAscii_Simple(Object, Span`1)

1)    at NUnit.Framework.Legacy.ClassicAssert.AreEqual(Object expected, Object actual)
   at Markdig.Tests.TestLinkHelper.TestUrilizeNonAscii_Simple(String input, String expectedResult) in <worktree>/src/Markdig.Tests/TestLinkHelper.cs:line 370
   at InvokeStub_TestLinkHelper.TestUrilizeNonAscii_Simple(Object, Span`1)


  Failed TestUrilizeNonAscii_Simple("-fr-ø","fr-ø") [< 1 ms]
  Error Message:
     Assert.That(actual, Is.EqualTo(expected))
  Expected string length 4 but was 5. Strings differ at index 3.
  Expected: "fr-ø"
  But was:  "fr-oe"
  --------------^

  Stack Trace:
     at NUnit.Framework.Legacy.ClassicAssert.AreEqual(Object expected, Object actual)
   at Markdig.Tests.TestLinkHelper.TestUrilizeNonAscii_Simple(String input, String expectedResult) in <worktree>/src/Markdig.Tests/TestLinkHelper.cs:line 370
   at InvokeStub_TestLinkHelper.TestUrilizeNonAscii_Simple(Object, Span`1)

1)    at NUnit.Framework.Legacy.ClassicAssert.AreEqual(Object expected, Object actual)
   at Markdig.Tests.TestLinkHelper.TestUrilizeNonAscii_Simple(String input, String expectedResult) in <worktree>/src/Markdig.Tests/TestLinkHelper.cs:line 370
   at InvokeStub_TestLinkHelper.TestUrilizeNonAscii_Simple(Object, Span`1)


  Failed TestUrilizeOnlyAscii_NonAscii("bær","br") [< 1 ms]
  Error Message:
     Assert.That(actual, Is.EqualTo(expected))
  Expected string length 2 but was 4. Strings differ at index 1.
  Expected: "br"
  But was:  "baer"
  ------------^

  Stack Trace:
     at NUnit.Framework.Legacy.ClassicAssert.AreEqual(Object expected, Object actual)
   at Markdig.Tests.TestLinkHelper.TestUrilizeOnlyAscii_NonAscii(String input, String expectedResult) in <worktree>/src/Markdig.Tests/TestLinkHelper.cs:line 336

1)    at NUnit.Framework.Legacy.ClassicAssert.AreEqual(Object expected, Object actual)
   at Markdig.Tests.TestLinkHelper.TestUrilizeOnlyAscii_NonAscii(String input, String expectedResult) in <worktree>/src/Markdig.Tests/TestLinkHelper.cs:line 336


  Failed TestUrilizeOnlyAscii_NonAscii("bør","br") [< 1 ms]
  Error Message:
     Assert.That(actual, Is.EqualTo(expected))
  Expected string length 2 but was 4. Strings differ at index 1.
  Expected: "br"
  But was:  "boer"
  ------------^

  Stack Trace:
     at NUnit.Framework.Legacy.ClassicAssert.AreEqual(Object expected, Object actual)
   at Markdig.Tests.TestLinkHelper.TestUrilizeOnlyAscii_NonAscii(String input, String expectedResult) in <worktree>/src/Markdig.Tests/TestLinkHelper.cs:line 336
   at InvokeStub_TestLinkHelper.TestUrilizeOnlyAscii_NonAscii(Object, Span`1)

1)    at NUnit.Framework.Legacy.ClassicAssert.AreEqual(Object expected, Object actual)
   at Markdig.Tests.TestLinkHelper.TestUrilizeOnlyAscii_NonAscii(String input, String expectedResult) in <worktree>/src/Markdig.Tests/TestLinkHelper.cs:line 336
   at InvokeStub_TestLinkHelper.TestUrilizeOnlyAscii_NonAscii(Object, Span`1)



Failed!  - Failed:     7, Passed:    83, Skipped:     0, Total:    90, Duration: 69 ms - Markdig.Tests.dll (net9.0)
</test_output>

<test_snippet path="src/Markdig.Tests/TestLinkHelper.cs" lines="305-396">
    [TestCase("a c", "a-c")]
    [TestCase("a_c", "a_c")]
    [TestCase("a.c", "a.c")]
    [TestCase("a,c", "ac")]
    [TestCase("a--", "a")] // Not Pandoc-equivalent: a--
    [TestCase("a__", "a")] // Not Pandoc-equivalent: a__
    [TestCase("a..", "a")] // Not Pandoc-equivalent: a..
    [TestCase("a??", "a")]
    [TestCase("a  ", "a")]
    [TestCase("a--d", "a-d")]
    [TestCase("a__d", "a_d")]
    [TestCase("a??d", "ad")]
    [TestCase("a  d", "a-d")]
    [TestCase("a..d", "a.d")]
    [TestCase("-bc", "bc")]
    [TestCase("_bc", "bc")]
    [TestCase(" bc", "bc")]
    [TestCase("?bc", "bc")]
    [TestCase(".bc", "bc")]
    [TestCase("a-.-", "a")] // Not Pandoc equivalent: a-.-
    public void TestUrilizeOnlyAscii_Simple(string input, string expectedResult)
    {
        Assert.AreEqual(expectedResult, LinkHelper.Urilize(input, true));
    }

    [TestCase("bær", "br")]
    [TestCase("bør", "br")]
    [TestCase("bΘr", "br")]
    [TestCase("四五", "")]
    public void TestUrilizeOnlyAscii_NonAscii(string input, string expectedResult)
    {
        Assert.AreEqual(expectedResult, LinkHelper.Urilize(input, true));
    }

    [TestCase("bár", "bar")]
    [TestCase("àrrivé", "arrive")]
    public void TestUrilizeOnlyAscii_Normalization(string input, string expectedResult)
    {
        Assert.AreEqual(expectedResult, LinkHelper.Urilize(input, true));
    }

    [TestCase("123", "")]
    [TestCase("1,-b", "b")]
    [TestCase("b1,-", "b1")] // Not Pandoc equivalent: b1-
    [TestCase("ab3", "ab3")]
    [TestCase("ab3de", "ab3de")]
    public void TestUrilizeOnlyAscii_Numeric(string input, string expectedResult)
    {
        Assert.AreEqual(expectedResult, LinkHelper.Urilize(input, true));
    }

    [TestCase("一二三四五", "一二三四五")]
    [TestCase("一,-b", "一-b")]
    public void TestUrilizeNonAscii_NonAsciiNumeric(string input, string expectedResult)
    {
        Assert.AreEqual(expectedResult, LinkHelper.Urilize(input, false));
    }

    [TestCase("bær", "bær")]
    [TestCase("æ5el", "æ5el")]
    [TestCase("-æ5el", "æ5el")]
    [TestCase("-frø-", "frø")]
    [TestCase("-fr-ø", "fr-ø")]
    public void TestUrilizeNonAscii_Simple(string input, string expectedResult)
    {
        Assert.AreEqual(expectedResult, LinkHelper.Urilize(input, false));
    }

    // Just to be sure, test for characters expressly forbidden in URI fragments:
    [TestCase("b#r", "br")]
    [TestCase("b%r", "br")] // Invalid except as an escape character
    [TestCase("b^r", "br")]
    [TestCase("b[r", "br")]
    [TestCase("b]r", "br")]
    [TestCase("b{r", "br")]
    [TestCase("b}r", "br")]
    [TestCase("b<r", "br")]
    [TestCase("b>r", "br")]
    [TestCase(@"b\r", "br")]
    [TestCase(@"b""r", "br")]
    [TestCase(@"Requirement 😀", "requirement")]
    public void TestUrilizeNonAscii_NonValidCharactersForFragments(string input, string expectedResult)
    {
        Assert.AreEqual(expectedResult, LinkHelper.Urilize(input, false));
    }

    [Test]
    public void TestUnicodeInDomainNameOfLinkReferenceDefinition()
    {
        TestParser.TestSpec("[Foo]\n\n[Foo]: http://ünicode.com", "<p><a href=\"http://xn--nicode-2ya.com\">Foo</a></p>");
    }
}
</test_snippet>

<production_snippet path="src/Markdig/Helpers/LinkHelper.cs" lines="1-91">
// Copyright (c) Alexandre Mutel. All rights reserved.
// This file is licensed under the BSD-Clause 2 license. 
// See the license.txt file in the project root for more information.

using Markdig.Syntax;
using System.Buffers;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Globalization;
using System.Runtime.CompilerServices;
using System.Text;

namespace Markdig.Helpers;

/// <summary>
/// Helpers to parse Markdown links.
/// </summary>
public static class LinkHelper
{
    public static bool TryParseAutolink(StringSlice text, [NotNullWhen(true)] out string? link, out bool isEmail)
    {
        return TryParseAutolink(ref text, out link, out isEmail);
    }

    public static string Urilize(string headingText, bool allowOnlyAscii, bool keepOpeningDigits = false)
    {
        return Urilize(headingText.AsSpan(), allowOnlyAscii, keepOpeningDigits);
    }

    public static string Urilize(ReadOnlySpan<char> headingText, bool allowOnlyAscii, bool keepOpeningDigits = false)
    {
        var headingBuffer = new ValueStringBuilder(stackalloc char[ValueStringBuilder.StackallocThreshold]);
        bool hasLetter = keepOpeningDigits && headingText.Length > 0 && char.IsLetterOrDigit(headingText[0]);
        bool previousIsSpace = false;

        // First normalize the string to decompose characters if allowOnlyAscii is true
        string normalizedString = string.Empty;
        if (allowOnlyAscii)
        {
            normalizedString = headingText.ToString().Normalize(NormalizationForm.FormD);
        }

        var textToProcess = string.IsNullOrEmpty(normalizedString) ? headingText : normalizedString.AsSpan();

        for (int i = 0; i < textToProcess.Length; i++)
        {
            var c = textToProcess[i];

            // Skip combining diacritical marks when normalized
            if (allowOnlyAscii && CharUnicodeInfo.GetUnicodeCategory(c) == UnicodeCategory.NonSpacingMark)
            {
                continue;
            }

            // Handle German umlauts and Norwegian/Danish characters explicitly (they don't decompose properly)
            ReadOnlySpan<char> normalized;
            if (IsSpecialScandinavianOrGermanChar(c))
            {
                normalized = NormalizeScandinavianOrGermanChar(c);
            }
            else
            {
                normalized = allowOnlyAscii ? CharNormalizer.ConvertToAscii(c) : null;
            }

            for (int j = 0; j < (normalized.Length < 1 ? 1 : normalized.Length); j++)
            {
                if (normalized != null)
                {
                    c = normalized[j];
                }

                if (char.IsLetter(c))
                {
                    if (allowOnlyAscii && (c < ' ' || c >= 127))
                    {
                        continue;
                    }
                    c = char.IsUpper(c) ? char.ToLowerInvariant(c) : c;
                    headingBuffer.Append(c);
                    hasLetter = true;
                    previousIsSpace = false;
                }
                else if (hasLetter)
                {
                    if (IsReservedPunctuation(c))
                    {
                        if (previousIsSpace)
                        {
                            headingBuffer.Length--;
                        }
</production_snippet>

<production_snippet path="src/Markdig/Helpers/LinkHelper.cs" lines="108-201">
                            headingBuffer.Append('-');
                        }
                        previousIsSpace = true;
                    }
                }
            }
        }

        // Trim trailing _ - .
        while (headingBuffer.Length > 0)
        {
            var c = headingBuffer[headingBuffer.Length - 1];
            if (IsReservedPunctuation(c))
            {
                headingBuffer.Length--;
            }
            else
            {
                break;
            }
        }

        return headingBuffer.ToString();
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    private static bool IsSpecialScandinavianOrGermanChar(char c)
    {
        // German umlauts and ß
        // Norwegian/Danish/Swedish æ, ø, å
        // Icelandic þ (thorn), ð (eth)
        return c == 'ä' || c == 'ö' || c == 'ü' ||
               c == 'Ä' || c == 'Ö' || c == 'Ü' ||
               c == 'ß' ||
               c == 'æ' || c == 'ø' || c == 'å' ||
               c == 'Æ' || c == 'Ø' || c == 'Å' ||
               c == 'þ' || c == 'ð' ||
               c == 'Þ' || c == 'Ð';
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    private static ReadOnlySpan<char> NormalizeScandinavianOrGermanChar(char c)
    {
        return c switch
        {
            // German
            'ä' => "ae",
            'ö' => "oe",
            'ü' => "ue",
            'Ä' => "Ae",
            'Ö' => "Oe",
            'Ü' => "Ue",
            'ß' => "ss",
            // Norwegian/Danish/Swedish
            'æ' => "ae",
            'ø' => "oe",
            'å' => "aa",
            'Æ' => "Ae",
            'Ø' => "Oe",
            'Å' => "Aa",
            // Icelandic
            'þ' => "th",
            'Þ' => "Th",
            'ð' => "d",
            'Ð' => "D",
            _ => ReadOnlySpan<char>.Empty
        };
    }

    public static string UrilizeAsGfm(string headingText)
    {
        return UrilizeAsGfm(headingText.AsSpan());
    }

    public static string UrilizeAsGfm(ReadOnlySpan<char> headingText)
    {
        // Following https://github.com/jch/html-pipeline/blob/master/lib/html/pipeline/toc_filter.rb
        var headingBuffer = new ValueStringBuilder(stackalloc char[ValueStringBuilder.StackallocThreshold]);
        for (int i = 0; i < headingText.Length; i++)
        {
            var c = headingText[i];
            if (char.IsLetterOrDigit(c) || c == '-' || c == '_')
            {
                headingBuffer.Append(char.ToLowerInvariant(c));
            }
            else if (c == ' ')
            {
                headingBuffer.Append('-');
            }
        }
        return headingBuffer.ToString();
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
</production_snippet>

<production_snippet path="src/Markdig/Helpers/LinkHelper.cs" lines="269-303">
                isValidChar = true;
                // If this is not a special char valid also for url scheme, then we have an email
                if (!isSpecialChar)
                {
                    state = -1;
                }
            }

            if (isValidChar)
            {
                // a scheme is any sequence of 2–32 characters 
                if (state > 0 && builder.Length >= 32)
                {
                    goto ReturnFalse;
                }
                builder.Append(c);
            }
            else if (c == ':')
            {
                if (state < 0 || builder.Length <= 2)
                {
                    goto ReturnFalse;
                }
                state = 1;
                break;
            }
            else if (c == '@')
            {
                if (state > 0)
                {
                    goto ReturnFalse;
                }
                state = -1;
                break;
            }
</production_snippet>
