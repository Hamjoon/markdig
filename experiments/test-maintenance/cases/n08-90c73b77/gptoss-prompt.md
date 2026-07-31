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
index a994b3f2..82b3ff84 100644
--- a/src/Markdig/Helpers/LinkHelper.cs
+++ b/src/Markdig/Helpers/LinkHelper.cs
@@ -1006,7 +1006,7 @@ private static bool IsEndOfUri(char c, bool isAutoLink)
         return c == '\0' || c.IsSpaceOrTab() || c.IsControl() || (isAutoLink && c == '<'); // TODO: specs unclear. space is strict or relaxed? (includes tabs?)
     }
 
-    public static bool IsValidDomain(string link, int prefixLength, bool allowDomainWithoutPeriod)
+    public static bool IsValidDomain(string link, int prefixLength, bool allowDomainWithoutPeriod = false)
     {
         // https://github.github.com/gfm/#extended-www-autolink
         // A valid domain consists of alphanumeric characters, underscores (_), hyphens (-) and periods (.).
</recent_change_diff>

Current test results:
<test_output>
Test run for <worktree>/src/Markdig.Tests/bin/Release/net9.0/Markdig.Tests.dll (.NETCoreApp,Version=v9.0)
A total of 1 test files matched the specified pattern.
  Skipped ListUnorderedLooseTop [< 1 ms]

Passed!  - Failed:     0, Passed:  3453, Skipped:     1, Total:  3454, Duration: 1 s - Markdig.Tests.dll (net9.0)
</test_output>

<production_snippet path="src/Markdig/Helpers/LinkHelper.cs" lines="984-1034">
        if (isValid)
        {
            link = buffer.ToString();
        }
        else
        {
            buffer.Dispose();
            link = null;
        }
        return isValid;
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    private static bool IsTrailingUrlStopCharacter(char c)
    {
        // Trailing punctuation (specifically, ?, !, ., ,, :, *, _, and ~) will not be considered part of the autolink, though they may be included in the interior of the link:
        return c == '?' || c == '!' || c == '.' || c == ',' || c == ':' || c == '*' || c == '*' || c == '_' || c == '~';
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    private static bool IsEndOfUri(char c, bool isAutoLink)
    {
        return c == '\0' || c.IsSpaceOrTab() || c.IsControl() || (isAutoLink && c == '<'); // TODO: specs unclear. space is strict or relaxed? (includes tabs?)
    }

    public static bool IsValidDomain(string link, int prefixLength, bool allowDomainWithoutPeriod = false)
    {
        // https://github.github.com/gfm/#extended-www-autolink
        // A valid domain consists of alphanumeric characters, underscores (_), hyphens (-) and periods (.).
        // There must be at least one period, and no underscores may be present in the last two segments of the domain.

        // Extended as of https://github.com/lunet-io/markdig/issues/316 to accept non-ascii characters,
        // as long as they are not in the space or punctuation categories

        int segmentCount = 1;
        bool segmentHasCharacters = false;
        int lastUnderscoreSegment = -1;

        for (int i = prefixLength; i < link.Length; i++)
        {
            char c = link[i];

            if (c == '.') // New segment
            {
                if (!segmentHasCharacters)
                    return false;

                segmentCount++;
                segmentHasCharacters = false;
                continue;
            }
</production_snippet>
