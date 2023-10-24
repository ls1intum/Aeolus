import {Card, Grid} from "@mantine/core";
import ExplanationItem, {ExplanationItemProps} from "./ExplanationItem";
import React, {ReactElement} from "react";

function ExplanationsList() {
    const what_am_i_seeing: ExplanationItemProps = {
        explanationText: "Aeolus allows you to write a single definition of a CI job and translate it to work with multiple platforms",
        bash: "echo 'in bash code ⚙️'",
        jenkins: "stages('jenkins') {\n\tsteps {\n\t\techo 'or jenkins ⚙️'\n\t}\n}",
        bamboo: `bamboo: or in bamboo yaml specs`,
        bambooExplanation: "Why specs you ask? Because it's easier to generate and aeolus also allows you to directly " +
            "publish the jobs, so you don't have to work with the specs at all."
    };
    const items: ExplanationItemProps[] = [what_am_i_seeing];
    const list: ReactElement[] = items.map((item) =>
        <Card style={{
            width: "100%"
        }}>
            <Grid.Col span={12} key={item.explanationText}>
                <ExplanationItem key={item.explanationText} {...item}/>
            </Grid.Col>
        </Card>)
    return <Grid>{list}</Grid>;
}

export default ExplanationsList;