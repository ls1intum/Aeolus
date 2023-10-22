import React, {useEffect, useRef, useState} from 'react';
import {Editor} from "@monaco-editor/react";
import {configureMonacoYaml} from "monaco-yaml";
import {Grid, Title, useComputedColorScheme} from "@mantine/core";
import {CodeHighlightTabs} from "@mantine/code-highlight";
import BashIcon from "../icons/BashIcon";
import BambooIcon from "../icons/BambooIcon";
import JenkinsIcon from "../icons/JenkinsIcon";

interface PlaygroundProps {
}

function Playground(props: PlaygroundProps) {
    window.MonacoEnvironment = {
        getWorker(moduleId, label) {
            switch (label) {
                case 'editorWorkerService':
                    return new Worker(new URL('monaco-editor/esm/vs/editor/editor.worker', import.meta.url))
                case 'json':
                    return new Worker(
                        new URL('monaco-editor/esm/vs/language/json/json.worker', import.meta.url)
                    )
                case 'yaml':
                    return new Worker(new URL('monaco-yaml/yaml.worker.js?worker', import.meta.url))
                default:
                    throw new Error(`Unknown label ${label}`)
            }
        }
    }
    let default_windfile: string = `api: v0.0.1
metadata:
  name: example windfile
  id: example-windfile
  description: This is a windfile with an internal action
  author: Andreas Resch
  docker:
    image: ls1tum/artemis-maven-template
    tag: java17-20
    volumes:
      - $\{WORKDIR}:/aeolus
    parameters:
      - --cpus
      - '"2"'
      - --memory
      - '"2g"'
      - --memory-swap
      - '"2g"'
      - --pids-limit
      - '"1000"'
  gitCredentials: artemis_gitlab_admin_credentials
repositories:
  aeolus:
    url: https://github.com/ls1intum/Aeolus.git
    branch: develop
    path: aeolus
actions:
  set-java-container:
    script: set
  set-c-container:
    docker:
      image: ghcr.io/ls1intum/artemis-c-docker
    script: set
  internal-action:
    script: |
      echo "This is an internal action"
  clean_up:
    script: |
      rm -rf aeolus/
    run_always: true`;
    const [data, setData] = useState<string>(default_windfile);

    const monacoRef = useRef(null);

    function handleEditorWillMount(monaco: any) {
        // here is the monaco instance
        // do something before editor is mounted
        // monaco.languages.typescript.javascriptDefaults.setEagerModelSync(true);
        configureMonacoYaml(monaco, {
            enableSchemaRequest: true,
            schemas: [
                {
                    fileMatch: ['windfile.yaml'],
                    uri: 'https://raw.githubusercontent.com/ls1intum/Aeolus/develop/schemas/v0.0.1/schemas/windfile.json'
                },
            ]
        });
    }

    function handleEditorDidMount(editor: any, monaco: any) {
        // here is another way to get monaco instance
        // you can also store it in `useRef` for further usage
        monacoRef.current = monaco;
    }

    const computedColorScheme = useComputedColorScheme('light', {getInitialValueInEffect: true});
    const editorTheme: 'vs-dark' | 'light' = computedColorScheme === 'dark' ? 'vs-dark' : 'light';

    const bashIcon = <BashIcon size={24}/>;
    const bambooIcon = <BambooIcon size={24}/>;
    const jenkinsIcon = <JenkinsIcon size={24}/>;

    const [target, setTarget] = React.useState<"cli" | "jenkins" | "bamboo">('cli');
    const [input, setInput] = React.useState<string>(default_windfile);

    useEffect(() => {
        fetch('http://127.0.0.1:8000/generate/' + target + '/yaml', {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/x-yaml'
            },
            body: input,
        })
            .then(response => response.json())
            .catch(error => console.error('Error:', error))
            .then(data => setData(data.result));
    }, [target, input]);


    function handleEditorChange(value: string | undefined, _: any) {
        if (value === undefined) {
            setInput(default_windfile);
        } else {
            setInput(value);
        }
    }

    return (
        <Grid grow style={{
            margin: '16px',
        }} gutter="md">
            <Grid.Col span={6}>
                <Title style={{
                    margin: '4px',
                }} order={4}>Define your job:</Title>
                <Editor height="100vh" defaultLanguage="yaml" path="windfile.yaml"
                        defaultValue={default_windfile} theme={editorTheme} beforeMount={handleEditorWillMount}
                        onMount={handleEditorDidMount} onChange={handleEditorChange}/>
            </Grid.Col>
            <Grid.Col span={6}>
                <CodeHighlightTabs
                    onTabChange={(tab) => {
                        if (tab === 0) setTarget('cli');
                        if (tab === 1) setTarget('bamboo');
                        if (tab === 2) setTarget('jenkins');
                    }}
                    code={[
                        {
                            fileName: 'generated.sh',
                            code: data,
                            language: 'bash',
                            icon: bashIcon,
                        },
                        {
                            fileName: 'Bamboo Build Plan',
                            code: data,
                            language: 'yaml',
                            icon: bambooIcon,
                        },
                        {
                            fileName: 'Jenkinsfile',
                            code: data,
                            language: 'groovy',
                            icon: jenkinsIcon,
                        },
                    ]}
                >
                </CodeHighlightTabs>
                {/*<Group justify="center">*/}
                {/*    <Button leftSection={bashIcon} variant="default" onClick={() => setTarget('cli')}>*/}
                {/*        Bash*/}
                {/*    </Button>*/}
                {/*    <Button leftSection={bambooIcon} variant="default" onClick={() => setTarget('bamboo')}>*/}
                {/*        Bamboo*/}
                {/*    </Button>*/}
                {/*    <Button leftSection={jenkinsIcon} variant="default" onClick={() => setTarget('jenkins')}>*/}
                {/*        Jenkins*/}
                {/*    </Button>*/}
                {/*</Group>*/}
                {/*<CodeHighlight*/}
                {/*    code={data}*/}
                {/*    language={getCurrentLanguage()}*/}
                {/*/>*/}
            </Grid.Col>
        </Grid>
    );
}

export default Playground;
