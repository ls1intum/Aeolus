import React from 'react';
import {
    AppShell, Burger,
    ColorSchemeScript,
    Group,
    MantineProvider, Space, Title,
} from "@mantine/core";
import Playground from "./playground/Playground";
import ThemeSwitcher from "./themeSwitcher/ThemeSwitcher";
import {useDisclosure} from "@mantine/hooks";
import AeolusIcon from "./icons/AeolusIcon";
import ExplanationsList from "./explanations/ExplanationsList";

function App() {
    const [mobileOpened, {toggle: toggleMobile}] = useDisclosure();
    const [desktopOpened, {toggle: toggleDesktop}] = useDisclosure(false);
    return (
        <>
            <ColorSchemeScript defaultColorScheme="auto"/>
            <MantineProvider defaultColorScheme="auto" theme={{
                fontFamily: 'Verdana, sans-serif',
                fontFamilyMonospace: 'Monaco, Courier, monospace',
                headings: {fontFamily: 'Greycliff CF, sans-serif'},
            }}>
                <AppShell
                    header={{height: {base: 60, md: 70, lg: 80}}}
                    navbar={{
                        width: {base: 200, md: 300, lg: 400},
                        breakpoint: 'sm',
                        collapsed: {mobile: !mobileOpened, desktop: !desktopOpened},
                    }}
                    padding="md"
                >
                    <AppShell.Header>
                        <Group h="100%" px="md">
                            <Burger opened={mobileOpened} onClick={toggleMobile} hiddenFrom="sm" size="sm"/>
                            <Burger opened={desktopOpened} onClick={toggleDesktop} visibleFrom="sm" size="sm"/>
                            <AeolusIcon size={48}/>
                            <Title order={2}>Aeolus</Title>
                            <ThemeSwitcher/>
                        </Group>
                    </AppShell.Header>

                    <AppShell.Navbar p="md">
                    {/*    Navbar*/}
                    {/*    {Array(15)*/}
                    {/*        .fill(0)*/}
                    {/*        .map((_, index) => (*/}
                    {/*            <Skeleton key={index} h={28} mt="sm" animate={false}/>*/}
                    {/*        ))}*/}
                        nothing to see here
                    </AppShell.Navbar>

                    <AppShell.Main>
                        <Playground/>
                        <Space h="lg"/>
                        <ExplanationsList/>
                    </AppShell.Main>
                </AppShell>
            </MantineProvider>
        </>
    );
}

export default App;
