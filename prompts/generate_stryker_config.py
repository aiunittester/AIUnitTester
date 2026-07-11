STRYKER_CONFIG = """
{{
  "$schema": "{schema}",
  "packageManager": "yarn",
  "reporters": [
    "html",
    "json"
  ],
  "testRunner": "jest",
  "coverageAnalysis": "perTest",
  "mutate": {mutate},
  "mutator": {{
    "excludedMutations": [ ]
  }},
  "timeoutMS": 10000,
  "dryRunTimeoutMinutes": 100,
  "ignoreStatic": true
}}
"""
