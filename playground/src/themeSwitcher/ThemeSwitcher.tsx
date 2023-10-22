import {ActionIcon, useMantineColorScheme, useComputedColorScheme} from '@mantine/core';
import {IconSun, IconMoon} from '@tabler/icons-react';
import classes from './ThemeSwitcher.module.css';

function ThemeSwitcher() {
    const {setColorScheme} = useMantineColorScheme();
    const computedColorScheme = useComputedColorScheme('light', {getInitialValueInEffect: true});

    return (
        <ActionIcon
            onClick={() => setColorScheme(computedColorScheme === 'light' ? 'dark' : 'light')}
            variant="default"
            size="xl"
            aria-label="Toggle color scheme"
        >
            <IconSun className={classes.icon} style={{
                display: computedColorScheme === 'dark' ? 'block' : 'none',
            }} stroke={1.5}/>
            <IconMoon className={classes.icon} style={{
                display: computedColorScheme === 'light' ? 'block' : 'none',
            }} stroke={1.5}/>
        </ActionIcon>
    );
}

export default ThemeSwitcher;