You are maintaining a C#/.NET library. A change was recently applied to this repository.
Review the recent change and the current test results, then decide whether any modification
is needed: update tests, fix production code, or no change at all.

Constraints:
- The first line of your reply must be exactly one of: `DECISION: no_change`, `DECISION: fix_tests`, `DECISION: fix_production`.
- If the decision is `fix_tests` or `fix_production`, follow the DECISION line with a unified diff implementing the fix. If the decision is `no_change`, output no diff.
- Allowed files: src/Markdig/Extensions/MediaLinks/HostProviderBuilder.cs, src/Markdig/Extensions/MediaLinks/MediaOptions.cs, src/Markdig/Globals.cs, src/Markdig/Helpers/CharHelper.cs, src/Markdig/Helpers/CharNormalizer.cs, src/Markdig/Helpers/CharacterMap.cs.
- Do not weaken, delete, or skip assertions.
- Preserve nearby behavior that is still expected to pass.

Recent change applied to the repository:
<recent_change_diff>
diff --git a/src/Markdig/Extensions/MediaLinks/HostProviderBuilder.cs b/src/Markdig/Extensions/MediaLinks/HostProviderBuilder.cs
index 38377ac8..9b2e455c 100644
--- a/src/Markdig/Extensions/MediaLinks/HostProviderBuilder.cs
+++ b/src/Markdig/Extensions/MediaLinks/HostProviderBuilder.cs
@@ -55,16 +55,15 @@ public static IHostProvider Create(string hostPrefix, Func<Uri, string?> handler
         return new DelegateProvider(hostPrefix, handler, allowFullScreen, iframeClass);
     }
 
-    internal static Dictionary<string, IHostProvider> KnownHosts { get; }
-        = new Dictionary<string, IHostProvider>(StringComparer.OrdinalIgnoreCase)
-        {
-            ["YouTubeShort"] = Create("www.youtube.com", YouTubeShort, iframeClass: "youtubeshort"),
-            ["YouTube"] = Create("www.youtube.com", YouTube, iframeClass: "youtube"),
-            ["YouTubeShortened"] = Create("youtu.be", YouTubeShortened, iframeClass: "youtube"),
-            ["Vimeo"] = Create("vimeo.com", Vimeo, iframeClass: "vimeo"),
-            ["Yandex"] = Create("music.yandex.ru", Yandex, allowFullScreen: false, iframeClass: "yandex"),
-            ["Odnoklassniki"] = Create("ok.ru", Odnoklassniki, iframeClass: "odnoklassniki"),
-        };
+    internal static readonly IHostProvider[] KnownHosts =
+    [
+        Create("www.youtube.com", YouTubeShort, iframeClass: "youtubeshort"),
+        Create("www.youtube.com", YouTube, iframeClass: "youtube"),
+        Create("youtu.be", YouTubeShortened, iframeClass: "youtube"),
+        Create("vimeo.com", Vimeo, iframeClass: "vimeo"),
+        Create("music.yandex.ru", Yandex, allowFullScreen: false, iframeClass: "yandex"),
+        Create("ok.ru", Odnoklassniki, iframeClass: "odnoklassniki"),
+    ];
 
     #region Known providers
 
diff --git a/src/Markdig/Extensions/MediaLinks/MediaOptions.cs b/src/Markdig/Extensions/MediaLinks/MediaOptions.cs
index de682e69..2a22fd21 100644
--- a/src/Markdig/Extensions/MediaLinks/MediaOptions.cs
+++ b/src/Markdig/Extensions/MediaLinks/MediaOptions.cs
@@ -81,7 +81,7 @@ public MediaOptions()
             {".au", "audio/basic"},
             {".wav", "audio/x-wav"},
         };
-        Hosts = new List<IHostProvider>(HostProviderBuilder.KnownHosts.Values);
+        Hosts = new List<IHostProvider>(HostProviderBuilder.KnownHosts);
     }
 
     public string Width { get; set; }
diff --git a/src/Markdig/Globals.cs b/src/Markdig/Globals.cs
index 1a8b91ba..ed1c0bd4 100644
--- a/src/Markdig/Globals.cs
+++ b/src/Markdig/Globals.cs
@@ -1,2 +1,3 @@
 global using System;
+global using System.Collections.Frozen;
 global using System.Collections.Generic;
\ No newline at end of file
diff --git a/src/Markdig/Helpers/CharHelper.cs b/src/Markdig/Helpers/CharHelper.cs
index 7e80bedb..3a035ff7 100644
--- a/src/Markdig/Helpers/CharHelper.cs
+++ b/src/Markdig/Helpers/CharHelper.cs
@@ -24,12 +24,6 @@ public static class CharHelper
     private const char LowSurrogateStart = '\udc00';
     private const char LowSurrogateEnd = '\udfff';
 
-    // We don't support LCDM
-    private static readonly Dictionary<char, int> romanMap = new Dictionary<char, int>(6) {
-        { 'i', 1 }, { 'v', 5 }, { 'x', 10 },
-        { 'I', 1 }, { 'V', 5 }, { 'X', 10 }
-    };
-
     [MethodImpl(MethodImplOptions.AggressiveInlining)]
     private static bool IsPunctuationException(char c) =>
         c is '−' or '-' or '†' or '‡';
@@ -101,8 +95,8 @@ public static int RomanToArabic(ReadOnlySpan<char> text)
         int result = 0;
         for (int i = 0; i < text.Length; i++)
         {
-            var candidate = romanMap[text[i]];
-            if ((uint)(i + 1) < text.Length && candidate < romanMap[text[i + 1]])
+            int candidate = RomanToArabic(text[i]);
+            if ((uint)(i + 1) < text.Length && candidate < RomanToArabic(text[i + 1]))
             {
                 result -= candidate;
             }
@@ -112,6 +106,20 @@ public static int RomanToArabic(ReadOnlySpan<char> text)
             }
         }
         return result;
+
+        // We don't support LCDM
+        [MethodImpl(MethodImplOptions.AggressiveInlining)]
+        static int RomanToArabic(char c)
+        {
+            Debug.Assert(IsRomanLetterPartial(c));
+
+            return (c | 0x20) switch
+            {
+                'i' => 1,
+                'v' => 5,
+                _ => 10
+            };
+        }
     }
 
     [MethodImpl(MethodImplOptions.AggressiveInlining)]
diff --git a/src/Markdig/Helpers/CharNormalizer.cs b/src/Markdig/Helpers/CharNormalizer.cs
index fc6ecffa..fddae10c 100644
--- a/src/Markdig/Helpers/CharNormalizer.cs
+++ b/src/Markdig/Helpers/CharNormalizer.cs
@@ -20,7 +20,7 @@ public static class CharNormalizer
     }
 
     // This table was generated by the app UnicodeNormDApp
-    private static readonly Dictionary<char, string> CodeToAscii = new(1269)
+    private static readonly FrozenDictionary<char, string> CodeToAscii = new Dictionary<char, string>(1269)
     {
         {'Ḋ', "D"},
         {'Ḍ', "D"},
@@ -1291,5 +1291,5 @@ public static class CharNormalizer
         {'｜', "|"},
         {'｝', "}"},
         {'～', "~"},
-    };
+    }.ToFrozenDictionary();
 }
\ No newline at end of file
diff --git a/src/Markdig/Helpers/CharacterMap.cs b/src/Markdig/Helpers/CharacterMap.cs
index 7980c973..73ed3322 100644
--- a/src/Markdig/Helpers/CharacterMap.cs
+++ b/src/Markdig/Helpers/CharacterMap.cs
@@ -4,7 +4,6 @@
 
 using System.Buffers;
 using System.Diagnostics;
-using System.Linq;
 using System.Runtime.CompilerServices;
 
 namespace Markdig.Helpers;
@@ -17,7 +16,7 @@ public sealed class CharacterMap<T> where T : class
 {
     private readonly SearchValues<char> _values;
     private readonly T[] _asciiMap;
-    private readonly Dictionary<uint, T>? _nonAsciiMap;
+    private readonly FrozenDictionary<uint, T>? _nonAsciiMap;
 
     /// <summary>
     /// Initializes a new instance of the <see cref="CharacterMap{T}"/> class.
@@ -39,6 +38,7 @@ public CharacterMap(IEnumerable<KeyValuePair<char, T>> maps)
         Array.Sort(OpeningCharacters);
 
         _asciiMap = new T[128];
+        Dictionary<uint, T>? nonAsciiMap = null;
 
         foreach (var state in maps)
         {
@@ -49,16 +49,21 @@ public CharacterMap(IEnumerable<KeyValuePair<char, T>> maps)
             }
             else
             {
-                _nonAsciiMap ??= new Dictionary<uint, T>();
+                nonAsciiMap ??= [];
 
-                if (!_nonAsciiMap.ContainsKey(openingChar))
+                if (!nonAsciiMap.ContainsKey(openingChar))
                 {
-                    _nonAsciiMap[openingChar] = state.Value;
+                    nonAsciiMap[openingChar] = state.Value;
                 }
             }
         }
 
         _values = SearchValues.Create(OpeningCharacters);
+
+        if (nonAsciiMap is not null)
+        {
+            _nonAsciiMap = nonAsciiMap.ToFrozenDictionary();
+        }
     }
 
     /// <summary>
</recent_change_diff>

Current test results:
<test_output>
Test run for <worktree>/src/Markdig.Tests/bin/Release/net9.0/Markdig.Tests.dll (.NETCoreApp,Version=v9.0)
A total of 1 test files matched the specified pattern.
  Skipped ListUnorderedLooseTop [< 1 ms]

Passed!  - Failed:     0, Passed:  3453, Skipped:     1, Total:  3454, Duration: 1 s - Markdig.Tests.dll (net9.0)
</test_output>

<production_snippet path="src/Markdig/Extensions/MediaLinks/HostProviderBuilder.cs" lines="33-91">
                return false;
            }
            iframeUrl = Delegate(mediaUri);
            return !string.IsNullOrEmpty(iframeUrl);
        }
    }

    /// <summary>
    /// Create a <see cref="IHostProvider"/> with delegate handler.
    /// </summary>
    /// <param name="hostPrefix">Prefix of host that can be handled.</param>
    /// <param name="handler">Handler that generate iframe url, if uri cannot be handled, it can return <see langword="null"/>.</param>
    /// <param name="allowFullScreen">Should the generated iframe has allowfullscreen attribute.</param>
    /// <param name="iframeClass">"class" attribute of generated iframe.</param>
    /// <returns>A <see cref="IHostProvider"/> with delegate handler.</returns>
    public static IHostProvider Create(string hostPrefix, Func<Uri, string?> handler, bool allowFullScreen = true, string? iframeClass = null)
    {
        if (string.IsNullOrEmpty(hostPrefix))
            ThrowHelper.ArgumentException("hostPrefix is null or empty.", nameof(hostPrefix));
        if (handler is null)
            ThrowHelper.ArgumentNullException(nameof(handler));

        return new DelegateProvider(hostPrefix, handler, allowFullScreen, iframeClass);
    }

    internal static readonly IHostProvider[] KnownHosts =
    [
        Create("www.youtube.com", YouTubeShort, iframeClass: "youtubeshort"),
        Create("www.youtube.com", YouTube, iframeClass: "youtube"),
        Create("youtu.be", YouTubeShortened, iframeClass: "youtube"),
        Create("vimeo.com", Vimeo, iframeClass: "vimeo"),
        Create("music.yandex.ru", Yandex, allowFullScreen: false, iframeClass: "yandex"),
        Create("ok.ru", Odnoklassniki, iframeClass: "odnoklassniki"),
    ];

    #region Known providers

    private static readonly string[] SplitAnd = ["&"];
    private static string[] SplitQuery(Uri uri)
    {
        var query = uri.Query.Substring(uri.Query.IndexOf('?') + 1);
        return query.Split(SplitAnd, StringSplitOptions.RemoveEmptyEntries);
    }

    private static string? YouTube(Uri uri)
    {
        string uriPath = uri.AbsolutePath;
        if (string.Equals(uriPath, "/embed", StringComparison.OrdinalIgnoreCase) || uriPath.StartsWith("/embed/", StringComparison.OrdinalIgnoreCase))
        {
            return uri.ToString();
        }
        if (!string.Equals(uriPath, "/watch", StringComparison.OrdinalIgnoreCase) && !uriPath.StartsWith("/watch/", StringComparison.OrdinalIgnoreCase))
        {
            return null;
        }
        var queryParams = SplitQuery(uri);
        return BuildYouTubeIframeUrl(
            queryParams.FirstOrDefault(p => p.StartsWith("v=", StringComparison.Ordinal))?.Substring(2),
            queryParams.FirstOrDefault(p => p.StartsWith("t=", StringComparison.Ordinal))?.Substring(2)
</production_snippet>

<production_snippet path="src/Markdig/Extensions/MediaLinks/MediaOptions.cs" lines="59-98">
            {".eol", "audio/vnd.digital-winds"},
            {".dra", "audio/vnd.dra"},
            {".dts", "audio/vnd.dts"},
            {".dtshd", "audio/vnd.dts.hd"},
            {".rip", "audio/vnd.rip"},
            {".lvp", "audio/vnd.lucent.voice"},
            {".m3u", "audio/x-mpegurl"},
            {".pya", "audio/vnd.ms-playready.media.pya"},
            {".wma", "audio/x-ms-wma"},
            {".wax", "audio/x-ms-wax"},
            {".mid", "audio/midi"},
            {".mp3", "audio/mpeg"},
            {".mpga", "audio/mpeg"},
            {".mp4a", "audio/mp4"},
            {".ecelp4800", "audio/vnd.nuera.ecelp4800"},
            {".ecelp7470", "audio/vnd.nuera.ecelp7470"},
            {".ecelp9600", "audio/vnd.nuera.ecelp9600"},
            {".oga", "audio/ogg"},
            {".ogg", "audio/ogg"},
            {".weba", "audio/webm"},
            {".ram", "audio/x-pn-realaudio"},
            {".rmp", "audio/x-pn-realaudio-plugin"},
            {".au", "audio/basic"},
            {".wav", "audio/x-wav"},
        };
        Hosts = new List<IHostProvider>(HostProviderBuilder.KnownHosts);
    }

    public string Width { get; set; }

    public string Height { get; set; }

    public bool AddControlsProperty { get; set; }

    public string Class { get; set; }

    public Dictionary<string, string> ExtensionToMimeType { get; }

    public List<IHostProvider> Hosts { get; }
}
</production_snippet>

<production_snippet path="src/Markdig/Globals.cs" lines="1-3">
global using System;
global using System.Collections.Frozen;
global using System.Collections.Generic;
</production_snippet>

<production_snippet path="src/Markdig/Helpers/CharHelper.cs" lines="1-51">
// Copyright (c) Alexandre Mutel. All rights reserved.
// This file is licensed under the BSD-Clause 2 license. 
// See the license.txt file in the project root for more information.

using System.Diagnostics;
using System.Globalization;
using System.Runtime.CompilerServices;

namespace Markdig.Helpers;

/// <summary>
/// Helper class for handling characters.
/// </summary>
public static class CharHelper
{
    public const int TabSize = 4;

    public const char ReplacementChar = '\uFFFD';

    public const string ReplacementCharString = "\uFFFD";

    private const char HighSurrogateStart = '\ud800';
    private const char HighSurrogateEnd = '\udbff';
    private const char LowSurrogateStart = '\udc00';
    private const char LowSurrogateEnd = '\udfff';

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    private static bool IsPunctuationException(char c) =>
        c is '−' or '-' or '†' or '‡';

    public static void CheckOpenCloseDelimiter(char pc, char c, bool enableWithinWord, out bool canOpen, out bool canClose)
    {
        pc.CheckUnicodeCategory(out bool prevIsWhiteSpace, out bool prevIsPunctuation);
        c.CheckUnicodeCategory(out bool nextIsWhiteSpace, out bool nextIsPunctuation);

        var prevIsExcepted = prevIsPunctuation && IsPunctuationException(pc);
        var nextIsExcepted = nextIsPunctuation && IsPunctuationException(c);

        // A left-flanking delimiter run is a delimiter run that is
        // (1) not followed by Unicode whitespace, and either
        // (2a) not followed by a punctuation character or
        // (2b) followed by a punctuation character and preceded by Unicode whitespace or a punctuation character.
        // For purposes of this definition, the beginning and the end of the line count as Unicode whitespace.
        canOpen = !nextIsWhiteSpace &&
                       ((!nextIsPunctuation || nextIsExcepted) || prevIsWhiteSpace || prevIsPunctuation);


        // A right-flanking delimiter run is a delimiter run that is
        // (1) not preceded by Unicode whitespace, and either
        // (2a) not preceded by a punctuation character, or
        // (2b) preceded by a punctuation character and followed by Unicode whitespace or a punctuation character.
</production_snippet>

<production_snippet path="src/Markdig/Helpers/CharHelper.cs" lines="73-147">
    {
        // We don't support LCDM
        return IsRomanLetterLowerPartial(c) || IsRomanLetterUpperPartial(c);
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static bool IsRomanLetterLowerPartial(char c)
    {
        // We don't support LCDM
        return c == 'i' || c == 'v' || c == 'x';
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static bool IsRomanLetterUpperPartial(char c)
    {
        // We don't support LCDM
        return c == 'I' || c == 'V' || c == 'X';
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static int RomanToArabic(ReadOnlySpan<char> text)
    {
        int result = 0;
        for (int i = 0; i < text.Length; i++)
        {
            int candidate = RomanToArabic(text[i]);
            if ((uint)(i + 1) < text.Length && candidate < RomanToArabic(text[i + 1]))
            {
                result -= candidate;
            }
            else
            {
                result += candidate;
            }
        }
        return result;

        // We don't support LCDM
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        static int RomanToArabic(char c)
        {
            Debug.Assert(IsRomanLetterPartial(c));

            return (c | 0x20) switch
            {
                'i' => 1,
                'v' => 5,
                _ => 10
            };
        }
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static int AddTab(int column)
    {
        // return ((column + TabSize) / TabSize) * TabSize;
        Debug.Assert(TabSize == 4, "Change the AddTab implementation if TabSize is no longer a power of 2");
        return TabSize + (column & ~(TabSize - 1));
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static bool IsAcrossTab(int column)
    {
        return (column & (TabSize - 1)) != 0;
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static bool IsWhitespace(this char c)
    {
        // 2.1 Characters and lines
        // A Unicode whitespace character is any code point in the Unicode Zs general category,
        // or a tab (U+0009), line feed (U+000A), form feed (U+000C), or carriage return (U+000D).
        if (c <= ' ')
        {
            const long Mask =
</production_snippet>

<production_snippet path="src/Markdig/Helpers/CharNormalizer.cs" lines="1-48">
// Copyright (c) Alexandre Mutel. All rights reserved.
// This file is licensed under the BSD-Clause 2 license. 
// See the license.txt file in the project root for more information.

namespace Markdig.Helpers;

/// <summary>
/// Class used to simplify a unicode char to a simple ASCII string
/// </summary>
public static class CharNormalizer
{
    /// <summary>
    /// Converts a unicode char to a simple ASCII string.
    /// </summary>
    /// <param name="c">The input char.</param>
    /// <returns>The simple ASCII string or null if the char itself cannot be simplified</returns>
    public static string? ConvertToAscii(char c)
    {
        return c >= 160 && CodeToAscii.TryGetValue(c, out string? str) ? str : null;
    }

    // This table was generated by the app UnicodeNormDApp
    private static readonly FrozenDictionary<char, string> CodeToAscii = new Dictionary<char, string>(1269)
    {
        {'Ḋ', "D"},
        {'Ḍ', "D"},
        {'È', "E"},
        {'Ē', "E"},
        {'Ḕ', "E"},
        {'ª', "a"},
        {'²', "2"},
        {'³', "3"},
        {'¹', "1"},
        {'º', "o"},
        {'¼', "14"},
        {'½', "12"},
        {'¾', "34"},
        {'À', "A"},
        {'Á', "A"},
        {'Â', "A"},
        {'Ã', "A"},
        {'Ä', "A"},
        {'Å', "A"},
        {'Ç', "C"},
        {'É', "E"},
        {'Ê', "E"},
        {'Ë', "E"},
        {'Ì', "I"},
</production_snippet>

<production_snippet path="src/Markdig/Helpers/CharNormalizer.cs" lines="1269-1295">
        {'ｆ', "f"},
        {'ｇ', "g"},
        {'ｈ', "h"},
        {'ｉ', "i"},
        {'ｊ', "j"},
        {'ｋ', "k"},
        {'ｌ', "l"},
        {'ｍ', "m"},
        {'ｎ', "n"},
        {'ｏ', "o"},
        {'ｐ', "p"},
        {'ｑ', "q"},
        {'ｒ', "r"},
        {'ｓ', "s"},
        {'ｔ', "t"},
        {'ｕ', "u"},
        {'ｖ', "v"},
        {'ｗ', "w"},
        {'ｘ', "x"},
        {'ｙ', "y"},
        {'ｚ', "z"},
        {'｛', "{"},
        {'｜', "|"},
        {'｝', "}"},
        {'～', "~"},
    }.ToFrozenDictionary();
}
</production_snippet>

<production_snippet path="src/Markdig/Helpers/CharacterMap.cs" lines="1-91">
// Copyright (c) Alexandre Mutel. All rights reserved.
// This file is licensed under the BSD-Clause 2 license. 
// See the license.txt file in the project root for more information.

using System.Buffers;
using System.Diagnostics;
using System.Runtime.CompilerServices;

namespace Markdig.Helpers;

/// <summary>
/// Allows to associate characters to a data structures and query efficiently for them.
/// </summary>
/// <typeparam name="T"></typeparam>
public sealed class CharacterMap<T> where T : class
{
    private readonly SearchValues<char> _values;
    private readonly T[] _asciiMap;
    private readonly FrozenDictionary<uint, T>? _nonAsciiMap;

    /// <summary>
    /// Initializes a new instance of the <see cref="CharacterMap{T}"/> class.
    /// </summary>
    /// <param name="maps">The states.</param>
    /// <exception cref="ArgumentNullException"></exception>
    public CharacterMap(IEnumerable<KeyValuePair<char, T>> maps)
    {
        if (maps is null) ThrowHelper.ArgumentNullException(nameof(maps));

        var charSet = new HashSet<char>();

        foreach (var map in maps)
        {
            charSet.Add(map.Key);
        }

        OpeningCharacters = [.. charSet];
        Array.Sort(OpeningCharacters);

        _asciiMap = new T[128];
        Dictionary<uint, T>? nonAsciiMap = null;

        foreach (var state in maps)
        {
            char openingChar = state.Key;
            if (openingChar < 128)
            {
                _asciiMap[openingChar] ??= state.Value;
            }
            else
            {
                nonAsciiMap ??= [];

                if (!nonAsciiMap.ContainsKey(openingChar))
                {
                    nonAsciiMap[openingChar] = state.Value;
                }
            }
        }

        _values = SearchValues.Create(OpeningCharacters);

        if (nonAsciiMap is not null)
        {
            _nonAsciiMap = nonAsciiMap.ToFrozenDictionary();
        }
    }

    /// <summary>
    /// Gets all the opening characters defined.
    /// </summary>
    public char[] OpeningCharacters { get; }

    /// <summary>
    /// Gets the list of parsers valid for the specified opening character.
    /// </summary>
    /// <param name="openingChar">The opening character.</param>
    /// <returns>A list of parsers valid for the specified opening character or null if no parsers registered.</returns>
    public T? this[uint openingChar]
    {
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        get
        {
            T[] asciiMap = _asciiMap;
            if (openingChar < (uint)asciiMap.Length)
            {
                return asciiMap[openingChar];
            }
            else
            {
                T? map = null;
</production_snippet>
