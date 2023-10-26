import {Grid, Paper, Text, Title} from "@mantine/core";
import React, {ReactElement} from "react";
import {CodeHighlight, CodeHighlightTabs} from "@mantine/code-highlight";
import BashIcon from "../icons/BashIcon";
import BambooIcon from "../icons/BambooIcon";
import JenkinsIcon from "../icons/JenkinsIcon";


export interface ExplanationItemProps {
    title: string,
    explanationText: string,
    inputCode?: string,
    bash?: string,
    bashExplanation?: string,
    jenkins?: string,
    jenkinsExplanation?: string,
    bamboo?: string,
    bambooExplanation?: string,
}

function ExplanationItem(props: ExplanationItemProps) {
    const leftHand: ReactElement = <>
        <Title order={3} mb="xl">{props.title}</Title>
        <Text>{props.explanationText}</Text>
        {props.inputCode ? <CodeHighlight code={props.inputCode} language="yaml"/> : <></>}
    </>;

    const bashIcon = <BashIcon size={24}/>;
    const bambooIcon = <BambooIcon size={24}/>;
    const jenkinsIcon = <JenkinsIcon size={24}/>;

    const codeTabs: any[] = [];
    if (props.bash) {
        codeTabs.push({
            fileName: 'generated.sh',
            code: props.bash,
            language: 'bash',
            icon: bashIcon,
        });
    }
    if (props.bamboo) {
        codeTabs.push(
            {
                fileName: 'Bamboo Build Plan',
                code: props.bamboo,
                language: 'yaml',
                icon: bambooIcon,
            });
    }
    if (props.jenkins) {
        codeTabs.push({
            fileName: 'Jenkinsfile',
            code: props.jenkins,
            language: 'groovy',
            icon: jenkinsIcon,
        });
    }

    const [explanation, setExplanation] = React.useState<"cli" | "jenkins" | "bamboo">('cli');


    const rightHand: ReactElement = <>
        <CodeHighlightTabs mb="xl"
                           onTabChange={(tab) => {
                               const filename: string = codeTabs[tab].fileName;
                               if (filename === 'generated.sh') setExplanation('cli');
                               else if (filename === 'Bamboo Build Plan') setExplanation('bamboo');
                               else if (filename === 'Jenkinsfile') setExplanation('jenkins');
                           }}
                           code={codeTabs}
        >
        </CodeHighlightTabs>
        {explanation === 'cli' ? <Text>{props.bashExplanation}</Text> : <></>}
        {explanation === 'bamboo' ? <Text>{props.bambooExplanation}</Text> : <></>}
        {explanation === 'jenkins' ? <Text>{props.jenkinsExplanation}</Text> : <></>}
    </>
    return <Paper shadow="xs" withBorder p="xl">
        <Grid style={{
            minHeight: "18vh"
        }}>
            <Grid.Col span={{base: 12, md: 6, lg: 6}}>
                {leftHand}
            </Grid.Col>
            <Grid.Col span={{base: 12, md: 6, lg: 6}}>
                {rightHand}
            </Grid.Col>
        </Grid>
    </Paper>;
}

export default ExplanationItem;