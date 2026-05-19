Feasibility Limitations

The project may be receiving reports that are valid (the bug and attack vector are real) and cite assets and impacts that are in scope, but there may be obstacles or barriers to executing the attack in the real world. In other words, there is a question about how feasible the attack really is. Conversely, there may also be mitigation measures that projects can take to prevent the impact of the bug, which are not feasible or would require unconventional action and hence, should not be used as reasons for downgrading a bug's severity.

Therefore, Immunefi has developed a set of feasibility limitation standards which by default states what security researchers, as well as projects, can or cannot cite when reviewing a bug report:

Chain Rollbacks
2 years ago
Not yet followed by anyone
Rolling back the chain to mitigate the impact or profitability of an attack (reverting the chain to a previous state)
Immunefi strongly recommends that projects do not downgrade a bug report’s impact, severity, or payout in cases where the bug’s impact or profitability may be limited by performing a chain rollback. 

Rollbacks will be more feasible for some projects than others. For projects that can easily and quickly perform rollbacks, and have concerns about not being able to cite rollbacks as a reason to downgrade a bug report, we recommend they use flat payment amounts for each impact instead of payment ranges which scale based on the bug report’s impact.

Reasons for this standard: 

A chain rollback is an extremely heavy-handed method to reverse a devastating hack in the wild. If a project is forced to perform a rollback to prevent the hack, this implies that the bug impact is catastrophic enough that it merits the highest critical payout for the project’s bug bounty program. The purpose of the bug bounty program is to avoid having to execute chain rollbacks in the wild to reverse hacks.
Not all rollbacks themselves are feasible or successful. 
If projects were able to cite rollbacks, then they would never pay out a maximum critical reward for funds at risk because rollbacks could always be cited as a reason to downgrade the bug report, meaning the maximum critical amount would be misleading. 
Example: 

If a bug report showed that hundreds of millions of dollars were at risk on a chain, and the project stated that it would be impossible for a blackhat to steal that amount of money because they could execute a chain rollback, it might be true but it is besides the point. As long as the bug report submission met the rest of the bug bounty program’s criteria, it would be eligible for the highest critical payout. 

Chain Rollbacks’ FAQ
What if a project could roll back the chain before the stolen funds could be bridged out?

Immunefi recommends the project pay as normal and not use this as a factor to downgrade the bug report. Otherwise, the stated payment amount for that impact is false, since in practice it would never need to be paid because rollbacks could always be claimed.

Smaller chains and more centralized chains have an easy time executing chain rollbacks. It may even be an intentional safety mechanism. Shouldn’t they be able to claim chain rollbacks as a reason to downgrade a bug report?

If a project intends to use chain rollbacks as a safety mechanism, then their bug bounty program should account for that by adjusting the reward amount for the severities or impacts which they intend to use chain rollbacks to prevent. Otherwise, this invalidates the objectivity of the bug bounty program, since the project can arbitrarily downgrade a bug report despite the terms laid out in their bug bounty program.

Should projects that use ‘Primacy of Impact’ be able to claim chain rollbacks as a reason to downgrade bug reports because this impact is what they use to determine bug report validity?

Primacy of Impact refers to when an in-scope impact occurs on an out-of-scope asset and how that bug report should then be considered in-scope. Primacy of Impact does not refer to how impact should be calculated. Impact is calculated separately from any feasibility limitations, such as chain rollbacks. 

If a project intends to use chain rollbacks as a means to prevent an impact then their bug bounty program should account for that by adjusting the reward amount for those severities or impacts.


Pre-Impact Bug Monitoring
2 years ago Updated
Not yet followed by anyone
The Difference Between Immunefi’s Standards On Repeatable Attacks & Pre-Impact Monitoring
Immunefi’s standard on repeatable attacks determines a bug report’s payout amount based on a project’s capacity to respond to any specific repeatable attack.

On the other hand, Immunefi’s standard on pre-impact monitoring determines how any specific means of detecting a bug exploit & preventing the impact before it even occurs is factored into a bug report’s evaluation.

These are distinct factors in a bug report. For example, Immunefi’s repeatable attack standard will always apply to repeatable attacks, even if the project has no monitoring. And Immunefi’s pre-impact monitoring standards will apply even if the bug exploit is not repeatable. As well, both these standards could apply together to a single bug report.

Automated Means Of Blocking Bug Exploits
The term ‘auto-block tool’ in this article refers to any automated tooling which would detect a specific bug exploit before its impact is achieved & fully prevent it.

In general, if a project can objectively prove that an auto-block tool would prevent a bug exploit with 100% certainty, then Immunefi considers this a valid reason to downgrade the bug report’s reward amount by one severity level.

Immunefi still recommends that projects reward bug reports which would be automatically prevented with 100% certainty because:

There may be variants of the exploit that the auto-block tool would not catch.
There may be costs or damages caused by using the auto-block tool which are avoided by fixing the bug.
When the code is updated in the future the bug exploit, or variants of it, may no longer be prevented.
Despite the existence of the auto-block tool, there is still an impactful bug in the code which needs to be fixed.
However, if a project does not fix the bug, then Immunefi considers it reasonable for the project not to reward the bug report.

Automated Means Of Detecting Bug Exploits
Immunefi will evaluate bug reports on a case-by-case basis if by a combination of human action in response to an automated bug exploit detection tool, the bug exploit would be prevented. This may or may not be sufficient reason to downgrade a bug report.

In general, in order to downgrade a bug report for this reason, projects are required to provide 100% objective certainty that they would fully prevent the bug exploit. Projects are also required to provide objective proof that an automated bug exploit detection tool would detect the specific bug exploit with 100% certainty. 

Some factors that Immunefi considers when evaluating a bug report of this type are whether the required human action:

Can be executed unilaterally by any one of multiple individuals who would all be alerted by the automated bug exploit detection tool, or, requires multiple individuals in order to be executed.
Is fast, simple, and easy to execute, as well as being harmless to the project and its users, or, is slow, complicated, hard to execute, potentially costly or harmful to the project or its users.
The time between when the bug exploit would be detected and when its impact would be achieved.
Cases of this type are often highly complex and subjective, and so will always be evaluated on a case-by-case basis. Request mediation from Immunefi when you need help with such a bug report.

Non-100% Certain Means Of Detecting Bug Exploits
In general, if a means of detecting a bug exploit before its impact is achieved cannot be done with 100% certainty, then it’s an invalid reason to downgrade a bug report. This includes human means of detecting bug exploits, such as the project’s community, developers, or privileged addresses like Validators noticing the bug exploit.

However, exceptions may be made. Such as if a project has historically detected the specific type of pre-impact transaction involved in a bug report and successfully executed the correct action in time to prevent its impact.

Requirements For Proof Of Automated Detection/Blocking Tools
Immunefi requires proof that the project’s automated bug exploit detection or blocking tool would catch a specific bug report in order for that bug report’s reward amount to be downgraded. 

Immunefi also requires that the project share the proof with the whitehat and/or Immunefi (in certain cases) who submitted the bug report under the principle that private transparency is necessary for trust and fairness in the process.

FAQ
Q: If a project’s auto-block tooling would catch the bug’s exploit with 100% certainty, then is it a known issue?

A: No. Known issues refer to when a specific vulnerability and its impacts are known in detail in advance. On its own, an auto-block tooling does not indicate whether any specific bug was known in advance.

If the bug is a known issue, then the burden of proof is on the project. See this article for more details on how projects can prove a bug is a known issue.

Q: If Flashbots, a private mempool, or other means can be used to fully bypass the project’s detection tool, can it still be used to downgrade a bug report?

A: No. If such a means could bypass the detection tool, then it’s not considered effective enough to allow the attack to be prevented.

Attack Investment Amount
2 years ago Updated
Not yet followed by anyone
Introduction
This article lays out our standards and philosophy for evaluating bug reports that require an investment amount in order to exploit the vulnerability. The standards below, which are broken down into categories, determine under what conditions a bug can or cannot be downgraded.

Attacks Which Utilize Flashloans
In general, attacks which require flashloans to make the attack feasible or utilize flashloans to increase its impact are valid only if there is sufficient liquidity, either at the time of bug report submission or there is expected to be sufficient liquidity within the next 12 months.

If the conditions required for the attack are not present at the time of submission but are expected to be present within the next 12 months, then the bug report is valid for the appropriate payment amount based on its severity and impact.

FAQ
Q: What if the flashloan amounts were higher in the past and are expected to be higher in the future than they are at the time of submission, would this increase a bug report’s evaluated impact?

A: No. Minimum payment amounts per severity exist to incentivize whitehats to submit bugs immediately instead of waiting for their impact to increase in order to receive a greater payout, because this waiting would risk the bug being exploited by a blackhat or being submitted by another whitehat first.
Attacks Which Require An Investment Of The Attacker’s Own Capital
In general, Immunefi does not consider the high investment amount required for an attack to be a valid reason to downgrade a bug report. There have been successful attacks in which the attackers utilized millions worth of USD in order to execute, such as the Venus Protocol Hack, and nation-state-backed attacks could feasibly utilize significantly more.

That said, attacks which require $100 million USD or more to execute will be considered on a case-by-case basis as an exception to this general principle.

FAQ
Q: What if spending such a large amount for an attack isn’t profitable?

A: If the attack is not profitable then it may be downgraded to the impact of Griefing. This is explained in depth here: When Is An Impactful Attack Downgraded To Griefing?

Q: Isn’t it too risky to expect an attacker to risk so much of their own money?

A: In general, the financial risk to the attacker is only a valid reason to downgrade a bug report payment when the risk extremely outweighs the reward. This is explained in depth here: Attacks With A Financial Risk To The Attacker

Q: What if the whitehat who submitted the bug couldn’t acquire that much capital themselves?

A: Bug report evaluations are based on what a blackhat could acquire, not on what the specific whitehat who submitted the bug report could acquire.

Q: What if low token liquidity would require the attacker to spend a long time to acquire the high investment amount required for the attack?

A: In general, if an attacker could acquire the amount needed for an attack over 12 months, then the attack is considered valid.

That said, if it’d take longer than 12 months or there are unusual circumstances, Immunefi will consider it on a case-by-case basis.
Attacks Using An Asset Under The Project’s Control
This category refers to attacks which require an investment of an asset that the project could either prevent the blackhat from acquiring or could lock or seize in some way.

In general, if a project’s means of stopping an attack depend on manually executing an emergency action then this is considered an invalid reason to downgrade a bug report. This is because the purpose of a bug bounty program is to avoid the need to manually execute emergency actions in live code.

However, in unusual or complex situations Immunefi will evaluate the bug report on a case-by-case basis.

When evaluating if an attack could even acquire the necessary capital, or how the project could stop the attack, we base our judgements on objective historical data as much as possible. Common data we’ll look into are:

Total CEX/DEX liquidity over the last 12 months.
When historically has an individual attempted to acquire large amounts of capital and what was the project’s reaction?
When historically has the project prevented an individual from acquiring large amounts of capital, and when has the project locked or seized an individual’s capital?
FAQ
Q: In totally novel situations where there is no historical basis how does Immunefi evaluate the situation?

A: Those situations are evaluated on a case-by-case basis.


Attacks With A Financial Risk To The Attacker
2 years ago Updated
Not yet followed by anyone
In general, the financial risk to the attacker is only a valid reason to downgrade a bug report payment if the risk massively outweighs the reward.

Blackhats are willing to risk their money when they believe there’s a chance they’ll make a profit, and they will take such risks in an intelligent and patient manner, just as often as they will take risks in a foolish manner. For example, in the very notable Nomad Bridge hack from August 2022, the hacker was willing to spend $350,000 in gas on a failed attack before continuing to attack Nomad Bridge until they were able to successfully siphon out $190m in funds. Blackhat tolerance for risk is extremely high. 

So, the low return on investment (ROI) of an attack is not a valid reason on its own to downgrade a bug report, unless there is also a significant financial risk to the attacker.

Neither is the high financial risk involved in an attack a valid reason to downgrade a bug report if the attack also has a high ROI.

In most cases, risk is at least partially subjective and must be evaluated on a case-by-case basis. That said, Immunefi bases its evaluations on objective data as far as possible. These are common questions Immunefi will investigate when evaluating risk:

What would cause the attack to fail?
What percentage of the attacker’s investment capital would they lose if the attack failed?
What conditions would cause the attacker to lose money from a failed attack?
Immunefi evaluates a bug report’s ROI and financial risk to the attacker only from an external user’s point of view, not based on information only the project would know or have access to. 

The reason for this is that an attacker’s decision on whether to exploit an impactful bug is based on the information they have available to them as an external, outside user. So, even if the project could prove that the risk extremely outweighs the reward based on the information they have available to them as insiders, this is irrelevant as to whether or not the attacker would try to exploit the impactful bug.


When Is An Impactful Attack Downgraded To Griefing?
2 years ago Updated
Not yet followed by anyone
This article refers to bug reports with a High or Critical severity impact that the attacker does not profit from at all and may be costly to execute.



In general, if an attacker can only cause a small amount of damage per dollar they spend, then the attack’s impact is downgraded to Griefing.

The baseline ratio for Griefing is any attack where it costs $1 to deal $10 or less in damage on an attack for which the attacker does not profit from.

In contrast, any attack where it costs $1 to deal $100 or more in damage on an attack for which the attacker does not profit from is not Griefing because this is sufficiently impactful to motivate a malicious blackhat to exploit. For example, Immunefi considers it sufficient motivation for a malicious attacker to spend $1,000 of their own capital if they can then destroy $100,000. Same for if they can spend $100,000 to destroy $10 million.|



For any attack that falls between these ratios, does not directly put funds at risk, or is otherwise not covered in this article, Immunefi will evaluate on a case-by-case basis. That said, these are common questions Immunefi will investigate when evaluating risk:

Could the attacker indirectly profit from the attack?
How serious is the 2nd order damage from the attack?
 

Question: Can a denial of service attack on an asset in scope be considered the impact ‘Griefing’?

Answer: Yes it can.

For example, if deposits can be DOS'd by an attacker by frontrunning a tx, causing the user’s transaction to fail, and requiring the user to make a subsequent transaction.

In this example, damage is being caused to the user in the form of funds lost due to the reverting transaction. Even though the state may return back to normal, the contract is put in a not-optimal state which would block normal function execution for any user. When the state is back to normal, the user would be able to call the function once again to complete it. What the attacker achieved was damage to the user by requiring them to send another transaction. There's no profit for the attacker apart from damaging the users or the protocol.

 


