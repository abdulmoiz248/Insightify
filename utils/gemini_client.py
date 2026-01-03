"""
Google Gemini AI client for generating insights and analysis.
"""

import os
from typing import Dict, Any, List
import google.generativeai as genai


class GeminiClient:
    """Client for interacting with Google Gemini API."""
    
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash", temperature: float = 0.7):
        """
        Initialize Gemini client.
        
        Args:
            api_key: Google Gemini API key
            model: Model name to use (default: gemini-1.5-flash)
            temperature: Temperature for generation (0.0-1.0)
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        self.temperature = temperature
    
    def generate_daily_insights(self, commit_data: Dict[str, Any]) -> str:
        """
        Generate insights for daily commit data.
        
        Args:
            commit_data: Dictionary containing daily commit statistics
            
        Returns:
            Generated insights as string
        """
        # Build prompt from data
        prompt = self._build_daily_prompt(commit_data)
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': self.temperature,
                    'max_output_tokens': 1000,
                },
                safety_settings=[
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_NONE",
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_NONE",
                    },
                ]
            )
            
            # Check if response was blocked
            if not response.text:
                # Fallback to basic analysis
                return self._generate_fallback_insights(commit_data)
            
            return response.text
        except Exception as e:
            print(f"Warning: AI generation failed ({str(e)}), using fallback analysis")
            return self._generate_fallback_insights(commit_data)
    
    def generate_monthly_insights(self, monthly_data: Dict[str, Any]) -> str:
        """
        Generate insights for monthly aggregated data.
        
        Args:
            monthly_data: Dictionary containing monthly statistics
            
        Returns:
            Generated insights as string
        """
        prompt = self._build_monthly_prompt(monthly_data)
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': self.temperature,
                    'max_output_tokens': 2000,
                },
                safety_settings=[
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_NONE",
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_NONE",
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_NONE",
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_NONE",
                    },
                ]
            )
            
            # Check if response was blocked
            if not response.text:
                print("⚠️  Warning: AI response was blocked, using fallback analysis")
                return self._generate_monthly_fallback(monthly_data)
            
            return response.text
        except Exception as e:
            print(f"⚠️  Warning: AI generation failed ({str(e)}), using fallback analysis")
            return self._generate_monthly_fallback(monthly_data)
    
    def _build_daily_prompt(self, data: Dict[str, Any]) -> str:
        """Build prompt for daily insights."""
        total_commits = data.get('total_commits', 0)
        repos = data.get('repositories', {})
        languages = data.get('languages', {})
        estimated_hours = data.get('estimated_hours', 0)
        commit_messages = data.get('commit_messages', [])
        previous_days = data.get('previous_days', [])
        
        # Extract commit messages for analysis - include full messages
        commit_msgs = "\n".join([f"  - [{msg['repo']}] {msg['message']}" for msg in commit_messages[:15]])
        
        # Identify repo types for better context
        leetcode_repos = [r for r in repos.keys() if 'leetcode' in r.lower() or 'problem' in r.lower() or 'attempt' in r.lower()]
        project_repos = [r for r in repos.keys() if r not in leetcode_repos]
        
        repo_context = ""
        if leetcode_repos:
            repo_context += f"\n**LeetCode/Practice Repos (problem-solving practice):** {', '.join(leetcode_repos)}"
        if project_repos:
            repo_context += f"\n**Project Repos:** {', '.join(project_repos)}"
        
        # Build context from previous days
        prev_context = ""
        if previous_days:
            # Get last 7 days summary
            prev_repos = set()
            prev_total_commits = 0
            prev_languages = set()
            prev_commit_count = []
            
            for day in previous_days:
                prev_total_commits += day.get('total_commits', 0)
                prev_repos.update(day.get('repositories', {}).keys())
                prev_languages.update(day.get('languages', {}).keys())
                prev_commit_count.append(day.get('total_commits', 0))
            
            avg_commits = prev_total_commits / len(previous_days) if previous_days else 0
            
            prev_context = f"""
**Last 7 Days Context:**
- Average commits/day: {avg_commits:.1f} (Today: {total_commits} commits)
- Total unique repos: {len(prev_repos)}
- Recent repos: {', '.join(list(prev_repos)[:5])}
- Languages used: {', '.join(prev_languages)}
- Daily commit pattern: {prev_commit_count[-5:]} (last 5 days)
"""
        
        prompt = f"""You are a brutally honest senior developer reviewing daily coding activity. Be direct, specific, and analyze the ACTUAL commit messages to understand what was accomplished. Use actual data points.

**Today's Data ({data.get('date', 'N/A')})**
Commits: {total_commits} | Time: {estimated_hours}h | Repos: {len(repos)} | Languages: {', '.join(languages.keys()) if languages else 'None'}
{repo_context}

{prev_context}

**Actual Commit Messages (READ THESE CAREFULLY):**
{commit_msgs if commit_msgs else "No commits today"}

**Active Repositories:**
{self._format_repos(repos)}

**IMPORTANT CONTEXT:**
- Repos with "LeetCode", "Attempts", "Problems" in name = Problem-solving practice (not projects to "complete")
- Commit messages with "Time: X ms" or "Memory: X MB" = LeetCode submissions showing performance metrics
- "LeetSync" commits = Automated sync from LeetCode platform
- "Added README" for problems = Problem documentation

Analyze this and respond in EXACTLY this format (no extra commentary):

Pattern Detection:
[2-3 sentences maximum] Be SPECIFIC about what's happening. Analyze the ACTUAL commit messages to understand the work:
- For LeetCode repos: How many problems solved? What's the difficulty? Performance metrics mentioned?
- For project repos: What features/fixes were implemented based on commit messages?
- Mention exact language split (e.g., "Python for algorithms")
- Compare to previous days: Is today's {total_commits} commits above/below the {avg_commits:.1f} avg?
Use the actual repo names and what the commit messages reveal about progress.

Red Flags:
[2-3 sentences maximum] SCRUTINIZE based on ACTUAL commit messages:
- Generic/vague messages (just "fix", "update" without context)?
- For projects: Revert commits, build fixes, or unclear changes?
- Low output compared to previous days?
- Too scattered across many repos without depth?
- For LeetCode: Just easy problems or avoiding challenges?
If you find specific issues, quote the actual commit message and explain why it's problematic. If truly clean, say "None detected - clear, descriptive commits showing professional habits."

Brutal Truth:
[1-2 sentences maximum] Give SPECIFIC insight based on what the commit messages ACTUALLY show:
- For LeetCode: "2 problems solved with good performance (0ms) - solid algorithmic practice" OR "Stuck on same problem type - diversify practice"
- For projects: Reference what feature/fix the commits show, e.g., "Auth system implementation based on commits X, Y - real progress" OR "3 'fix' commits without context - what are you fixing?"
- Compare to patterns: "Consistent with last week's pace" OR "Dropping off from {avg_commits:.1f} avg"
NO GENERIC RESPONSES. Be specific using actual commit messages and repo names.

CRITICAL: 
- READ the commit messages and understand what they mean
- Use ACTUAL repo names from the data
- Reference SPECIFIC commit messages 
- NO generic portfolio/job advice for LeetCode practice repos
- Distinguish between problem-solving practice and project development"""
        
        return prompt
    
    def _build_monthly_prompt(self, data: Dict[str, Any]) -> str:
        """Build prompt for monthly insights - strict learning mentor style."""
        total_commits = data.get('total_commits', 0)
        total_hours = data.get('total_hours', 0)
        active_days = data.get('active_days', 0)
        languages = data.get('languages', {})
        top_repos = data.get('top_repositories', [])
        streak = data.get('longest_streak', 0)
        total_days = data.get('total_days', 30)
        avg_commits = data.get('avg_commits_per_day', 0)
        
        prompt = f"""You are a brutally honest senior developer mentoring a university student who is actively learning to code and build projects. This is NOT about job hunting - it's about genuine skill growth, learning consistency, and building real understanding. Be direct, specific, and call out issues without sugarcoating. Frame everything around learning progress and skill development.

**Monthly Data ({data.get('month', 'N/A')})**
- Total Commits: {total_commits}
- Coding Time: {total_hours}h
- Active Days: {active_days}/{total_days} days
- Longest Streak: {streak} days
- Avg Commits/Day: {avg_commits}
- Repositories: {data.get('total_repos', 0)}

**Languages:**
{self._format_dict(languages)}

**Top Repositories:**
{self._format_list(top_repos)}

**Weekly Pattern:**
{self._format_dict(data.get('commits_by_week', {}))}

Provide your analysis in this EXACT structure (use markdown headers):

## Learning Progress Check
[2-3 sentences] Analyze the actual learning output. {active_days}/{total_days} days active - is this consistent practice or sporadic bursts? {total_commits} commits in {total_hours}h - are they grinding productively or just playing around? A streak of {streak} days shows discipline (or lack of it). Be specific with the numbers and what they reveal about learning habits.

## Skill Development Analysis
[2-3 sentences] Look at what they're actually learning. Working with {', '.join(list(languages.keys())[:3]) if languages else 'unknown languages'} across {data.get('total_repos', 0)} repos - is this focused skill-building or scattered experimentation? Reference specific repos from the top list. Call out if they're hopping between techs without mastering any, or if they're building real understanding through focused project work.

## Reality Check (What's Actually Happening)
[2-3 bullet points] Be brutally honest about learning patterns:
- Is the consistency showing real commitment or procrastination patterns?
- Are they building complete projects or abandoning things halfway?
- {streak} day streak with {active_days} active days - grinding or slacking?
Use actual repo names and numbers. If they're doing well, acknowledge it briefly. If not, call it out directly.

## What You Need to Do
[2-3 specific, actionable points] Give direct learning-focused advice:
- If consistency is low: "Code every day even if just 30 minutes - muscle memory matters"
- If scattered: "Finish [specific repo] before starting anything new - completion builds real skills"
- If too many languages: "Master one language deeply before jumping around"
Be specific based on actual weaknesses in their learning approach.

CRITICAL RULES:
- NO introductory sentences like "Here's my analysis" or "Let me review"
- NO concluding statements like "In summary" or "Overall"  
- Use ACTUAL repo names from the top repositories list
- Reference SPECIFIC numbers from the data
- Frame everything around LEARNING and SKILL GROWTH, not jobs/career
- Talk to them like a student learning, not an employee being reviewed
- Be encouraging but brutally honest about what's not working
- This is learning mentorship, not a performance review"""
        
        return prompt
    
    def _generate_fallback_insights(self, data: Dict[str, Any]) -> str:
        """Generate brutally honest insights when AI fails."""
        total_commits = data.get('total_commits', 0)
        repos = data.get('repositories', {})
        languages = data.get('languages', {})
        hours = data.get('estimated_hours', 0)
        previous_days = data.get('previous_days', [])
        commit_messages = data.get('commit_messages', [])
        
        if total_commits == 0:
            return "Pattern Detection:\nNo commits today - consistency builds skills.\n\nRed Flags:\nZero output means zero progress.\n\nBrutal Truth:\nDaily practice is what separates learners from wannabes."
        
        # Identify repo types
        leetcode_repos = [r for r in repos.keys() if 'leetcode' in r.lower() or 'problem' in r.lower() or 'attempt' in r.lower()]
        project_repos = [r for r in repos.keys() if r not in leetcode_repos]
        
        # Analyze commit messages more intelligently
        leetcode_solves = []
        vague_commits = []
        
        for msg in commit_messages[:15]:
            message = msg['message']
            message_lower = message.lower()
            repo = msg['repo']
            
            # Detect LeetCode problem solves
            if 'time:' in message_lower and 'memory:' in message_lower:
                leetcode_solves.append(f"{repo}: Problem solved")
            elif 'added readme' in message_lower and any(lc in repo.lower() for lc in ['leetcode', 'problem', 'attempt']):
                continue  # Skip README commits for LeetCode
            # Detect vague commits (but only for non-LeetCode repos)
            elif repo in project_repos and any(word in message_lower for word in ['fix', 'update', 'change', 'revert', 'added code']):
                if len(message.split()) < 4:
                    vague_commits.append(f"{repo}: '{message}'")
        
        # Build sections
        top_lang = max(languages.items(), key=lambda x: x[1])[0] if languages else "Unknown"
        repo_list = ', '.join(list(repos.keys())[:3])
        
        # Pattern Detection
        if leetcode_repos and not project_repos:
            work_type = "algorithmic practice"
            problems_count = len([m for m in commit_messages if 'time:' in m['message'].lower()])
            pattern = f"Pattern Detection:\n{total_commits} commits on {', '.join(leetcode_repos)} in {hours}h - {work_type}. Solved {problems_count} problems using {top_lang}. Focused burst."
        elif project_repos and not leetcode_repos:
            work_type = "project development"
            pattern = f"Pattern Detection:\n{total_commits} commits on {', '.join(project_repos)[:2]} in {hours}h - {work_type}. Primary language: {top_lang}. {'Slow pace' if hours > 3 and total_commits < 5 else 'Focused burst'}."
        else:
            work_type = "mixed practice/projects"
            pattern = f"Pattern Detection:\n{total_commits} commits across {len(repos)} repos in {hours}h - {work_type}. Primary language: {top_lang}."
        
        # Red Flags
        red_flags = []
        
        # Only flag vague commits for project repos
        if vague_commits:
            red_flags.append(f"Vague commit messages in projects: {', '.join(vague_commits[:2])} - write descriptive commits.")
        
        # Different standards for LeetCode vs projects
        if project_repos and hours > 3 and total_commits < 4:
            red_flags.append(f"{hours}h for {total_commits} commits on projects - low output suggests you're stuck.")
        
        if len(project_repos) > 4:
            red_flags.append(f"Working across {len(project_repos)} projects - focus on completing one.")
        
        # Check if stuck on same project (not LeetCode)
        if previous_days and project_repos:
            prev_project_repos = set()
            for day in previous_days[-3:]:
                day_repos = day.get('repositories', {}).keys()
                prev_project_repos.update([r for r in day_repos if 'leetcode' not in r.lower() and 'problem' not in r.lower()])
            
            stuck_repos = set(project_repos).intersection(prev_project_repos)
            if stuck_repos and len(stuck_repos) == len(project_repos) and len(project_repos) == 1:
                red_flags.append(f"Still on {list(stuck_repos)[0]} for multiple days - push to complete or move on.")
        
        red_flags_text = "Red Flags:\n" + " ".join(red_flags) if red_flags else "Red Flags:\nNone detected - clean, focused work showing good habits."
        
        # Brutal Truth - specific to work type
        if leetcode_repos and not project_repos:
            problems_solved = len([m for m in commit_messages if 'time:' in m['message'].lower()])
            if problems_solved >= 2:
                truth = f"Brutal Truth:\nSolid algorithmic practice - {problems_solved} problems solved. Keep the momentum and tackle harder problems."
            else:
                truth = f"Brutal Truth:\nOne problem isn't enough - aim for at least 2-3 daily to build real problem-solving skills."
        elif vague_commits and len(project_repos) == 1:
            truth = f"Brutal Truth:\nWorking on {list(project_repos)[0]} with vague commits - describe what you're actually fixing/adding."
        elif len(project_repos) > 3:
            truth = f"Brutal Truth:\nJumping between {len(project_repos)} projects - finish ONE complete project instead of having multiple incomplete ones."
        elif hours > 4 and total_commits < 3:
            truth = f"Brutal Truth:\n{hours}h for {total_commits} commits - identify and eliminate blockers, or you're just procrastinating."
        else:
            truth = f"Brutal Truth:\nSolid focused work on {repo_list} - keep this consistency going."
        
        return f"{pattern}\n\n{red_flags_text}\n\n{truth}"
    
    def _generate_monthly_fallback(self, data: Dict[str, Any]) -> str:
        """Generate fallback monthly insights when AI fails - student learning focused."""
        total_commits = data.get('total_commits', 0)
        total_hours = data.get('total_hours', 0)
        active_days = data.get('active_days', 0)
        total_days = data.get('total_days', 30)
        streak = data.get('longest_streak', 0)
        avg_commits = data.get('avg_commits_per_day', 0)
        languages = data.get('languages', {})
        top_repos = data.get('top_repositories', [])
        
        # Calculate engagement
        engagement_pct = (active_days / total_days * 100) if total_days > 0 else 0
        commits_per_hour = (total_commits / total_hours) if total_hours > 0 else 0
        
        # Learning Progress Check
        if engagement_pct >= 80:
            progress_rating = "crushing it with consistent practice"
        elif engagement_pct >= 60:
            progress_rating = "decent consistency but room to improve"
        elif engagement_pct >= 40:
            progress_rating = "inconsistent - learning happens with daily practice"
        else:
            progress_rating = "sporadic at best - real learning needs regular coding"
        
        progress = f"""## Learning Progress Check
{active_days}/{total_days} days active ({engagement_pct:.1f}% of the month) - {progress_rating}. {total_commits} commits in {total_hours}h equals {commits_per_hour:.1f} commits/hour. Longest streak: {streak} days shows your discipline level. Consistent practice builds muscle memory, sporadic coding doesn't."""
        
        # Skill Development
        top_lang = max(languages.items(), key=lambda x: x[1])[0] if languages else "Unknown"
        lang_count = len(languages)
        repo_count = len(top_repos)
        
        if repo_count > 10:
            focus_assessment = "way too scattered - jumping between projects kills deep learning"
        elif repo_count > 5:
            focus_assessment = "moderate spread - consider finishing a few projects completely"
        else:
            focus_assessment = "good focus - building depth through concentrated effort"
        
        technical = f"""## Skill Development Analysis
Working across {repo_count} repositories with {lang_count} languages (primary: {top_lang}). {focus_assessment}. Top projects: {', '.join(top_repos[:3]) if top_repos else 'None'}. Deep understanding comes from completing projects, not starting many."""
        
        # Reality Check
        issues = []
        if engagement_pct < 60:
            issues.append(f"Only {active_days}/{total_days} active days - you're not building the daily coding habit that accelerates learning")
        if streak < 5:
            issues.append(f"Longest streak is {streak} days - where's the discipline? Consistency compounds")
        if commits_per_hour < 0.5 and total_hours > 10:
            issues.append(f"{commits_per_hour:.1f} commits/hour across {total_hours}h - spending time without output suggests you're stuck or distracted")
        if repo_count > 8:
            issues.append(f"Touching {repo_count} repos this month - are you learning deeply or just dabbling?")
        
        if not issues:
            issues.append("Solid month of learning - keep the momentum going and push yourself harder")
        
        critical = "## Reality Check (What's Actually Happening)\n" + "\n".join([f"- {issue}" for issue in issues])
        
        # What You Need to Do
        changes = []
        if engagement_pct < 70:
            changes.append(f"Code every single day, even just 30 mins - you're at {engagement_pct:.1f}%, aim for 80%+")
        if streak < 7:
            changes.append(f"Build a 7+ day streak (current: {streak}) - daily practice is non-negotiable for real skill growth")
        if repo_count > 6:
            changes.append(f"Pick your top project ({top_repos[0] if top_repos else 'one project'}) and finish it completely before touching others")
        if lang_count > 3:
            changes.append(f"Focus on mastering {top_lang} before jumping to other languages - depth beats breadth when learning")
        
        if not changes:
            changes.append(f"Challenge yourself with harder projects in {top_lang} - growth comes from pushing limits")
        
        action = "## What You Need to Do\n" + "\n".join([f"- {change}" for change in changes])
        
        return f"{progress}\n\n{technical}\n\n{critical}\n\n{action}"
    
    @staticmethod
    def _format_dict(data: Dict) -> str:
        """Format dictionary for prompt."""
        if not data:
            return "None"
        return "\n".join([f"  - {k}: {v}" for k, v in sorted(data.items(), key=lambda x: x[1], reverse=True)])
    
    @staticmethod
    def _format_repos(repos: Dict) -> str:
        """Format repositories for prompt."""
        if not repos:
            return "None"
        result = []
        for name, info in sorted(repos.items(), key=lambda x: x[1]['commits_count'], reverse=True):
            result.append(f"  - {name}: {info['commits_count']} commits ({info['language']})")
        return "\n".join(result)
    
    @staticmethod
    def _format_list(items: List) -> str:
        """Format list for prompt."""
        if not items:
            return "None"
        return "\n".join([f"  - {item}" for item in items])
